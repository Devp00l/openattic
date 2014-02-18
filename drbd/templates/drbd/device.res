{% comment %}
 Copyright (C) 2011-2014, it-novum GmbH <community@open-attic.org>

 openATTIC is free software; you can redistribute it and/or modify it
 under the terms of the GNU General Public License as published by
 the Free Software Foundation; version 2.

 This package is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
{% endcomment %}

resource {{ Connection.name }} {
	protocol {{ Connection.protocol }};
	meta-disk  internal;
	device /dev/drbd{{ Connection.id }};
	
	{% if Connection.syncer_rate %}
	syncer {
		rate {{ Connection.syncer_rate }};
	}
	{% endif %}
	
	{% for endpoint in Endpoints %}
	on {{ endpoint.ipaddress.device.host.hostname }} {
		disk       {{ endpoint.path }};
		address    {{ endpoint.ipaddress.host_part }}:{{ Connection.port }};
	}
	{% endfor %}
}
