# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

import re
from os.path import exists
from time import time

from django.http       import HttpResponse, Http404
from django.shortcuts  import get_object_or_404
from systemd.procutils import invoke

from nagios.conf   import settings as nagios_settings
from nagios.models import Service, Graph

def graph(request, service_id, srcidx):
    serv  = get_object_or_404(Service, pk=int(service_id))

    srcidx = int(srcidx)
    try:
        graph = Graph.objects.get(pk=srcidx, command=serv.command)
    except Graph.DoesNotExist:
        graph = None
        indexes = [str(srcidx)]
    else:
        indexes = graph.fields.split(' ')

    perfdata = serv.perfdata
    if not perfdata:
        raise Http404("Performance data not available")

    rrdpath = nagios_settings.RRD_PATH % serv.description.replace(' ', '_').encode("UTF-8")
    if not exists(rrdpath):
        raise Http404("RRD file not found")

    start  = request.GET.get("start",  str(int(time() - 24*60*60)))
    end    = request.GET.get("end",    str(int(time())))
    height = int(request.GET.get("height", 150))
    width  = int(request.GET.get("width",  700))
    color  = request.GET.get("color",  "00AA00CC")

    graphtitle = serv.description
    if graph is not None and width >= 350:
        graphtitle += ' - ' + graph.title

    args = [
        "rrdtool", "graph", "-", "--start", start, "--end", end, "--height", str(height),
        "--width", str(width), "--imgformat", "PNG", "--title", graphtitle,
        ]

    if graph is None:
        # Try to match the unit of the current value
        m = re.match( '\d+(?:\.\d+)?(?P<unit>[^\d;]+)?(?:;.*)?', perfdata[srcidx][1] )
        if m:
            if m.group("unit"):
                args.extend([ "--vertical-label", m.group("unit") ])
    elif graph.verttitle:
        args.extend([ "--vertical-label", graph.verttitle ])

    # See the "for" loop below for that if statement. boils down to "get x if index == -x else index"
    maxlen = max( [ len( perfdata[ int(srcidx[1:]) if srcidx[0] == '-' else int(srcidx) ][0] )
                    for srcidx in indexes ] )

    args.append("COMMENT:  " + (" " * maxlen))

    if width >= 350:
        args.extend([
            "COMMENT:%8s " % "Cur",
            "COMMENT:%8s " % "Min",
            "COMMENT:%8s " % "Avg",
            "COMMENT:%8s \\j" % "Max",
            ])
    else:
        args.extend([
            "COMMENT:%8s " % "Cur",
            "COMMENT:%8s \\j" % "Avg",
            ])

    args.append("HRULE:0#000000")

    for srcidx in indexes:
        invert = False
        if srcidx[0] == '-':
            invert = True
            srcidx = int(srcidx[1:])
        else:
            srcidx = int(srcidx)

        args.append( "DEF:var%d=%s:%d:AVERAGE" % (srcidx, rrdpath, int(srcidx) + 1) )

        if not invert:
            args.append("AREA:var%d#%s:%-*s" % (srcidx, color, maxlen, perfdata[srcidx][0]))
        else:
            args.extend([
                "CDEF:var%dneg=var%d,-1,*" % (srcidx, srcidx),
                "AREA:var%dneg#%s:%-*s"    % (srcidx, color, maxlen, perfdata[srcidx][0]),
                ])


        if width >= 350:
            args.extend([
                "GPRINT:var%d:LAST:%%8.2lf%%s"     % srcidx,
                "GPRINT:var%d:MIN:%%8.2lf%%s"      % srcidx,
                "GPRINT:var%d:AVERAGE:%%8.2lf%%s"  % srcidx,
                "GPRINT:var%d:MAX:%%8.2lf%%s\\j"   % srcidx,
                ])
        else:
            args.extend([
                "GPRINT:var%d:LAST:%%8.2lf%%s"     % srcidx,
                "GPRINT:var%d:AVERAGE:%%8.2lf%%s\\j"  % srcidx,
                ])

        perfvalues = perfdata[srcidx][1].split(';')
        if len(perfvalues) > 1:
            # maybe we have curr;warn;crit;min;max
            warn = perfvalues[1]
            crit = perfvalues[2] if len(perfvalues) > 2 else None
            vmin = perfvalues[3] if len(perfvalues) > 3 else None
            vmax = perfvalues[4] if len(perfvalues) > 4 else None

            if warn is not None:
                args.append( "HRULE:%s#F0F700" % (warn * (-1 if invert else 1) ) )

            if crit is not None:
                args.append( "HRULE:%s#FF0000" % (crit * (-1 if invert else 1) ) )

            #if vmin is not None:
                #args.extend([ "-l", vmin ])

            #if vmax is not None:
                #args.extend([ "-u", vmax ])


    #print args

    ret, out, err = invoke(args, log=False, return_out_err=True)

    return HttpResponse( out, mimetype="image/png" )

