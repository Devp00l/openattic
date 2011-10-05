{% load i18n %}
Ext.namespace("Ext.oa");

Ext.oa.Drbd__Device_Panel = Ext.extend(Ext.grid.GridPanel, {
  initComponent: function(){
    var drbdDevGrid = this;
    Ext.apply(this, Ext.apply(this.initialConfig, {
      title: "{% trans 'DRBD' %}",
      buttons: [{
        text: "{% trans 'Add DRBD Device' %}",
        icon: MEDIA_URL + "/icons2/16x16/actions/add.png",
        handler: function(){
          var addwin = new Ext.Window({
            title: "{% trans 'Add DRBD Device' %}",
            layout: "fit",
            height: 300,
            width: 500,
            items: [{
              xtype: "form",
              defaults: {
                xtype: "textfield",
                anchor: '-20px'
              },
              items: [{
                fieldLabel: "{% trans 'Protocol' %}",
                name: "protocol",
                ref: 'protofield'
              }],
              buttons: [{
                text: 'Create DRBD Device',
                icon: MEDIA_URL + "/icons/accept.png",
                handler: function(self){
                  drbd__DrbdDevice.create({
                    'protocol': self.ownerCt.ownerCt.protofield.getValue()
                  }, function(provider, response){
                    if( response.result ){
                      drbdDevGrid.store.reload();
                      addwin.hide();
                    }
                  });
                }
              }, {
                text: "{% trans 'Cancel' %}",
                icon: MEDIA_URL + "/icons2/16x16/actions/gtk-cancel.png",
                handler: function(self){
                  addwin.hide();
                }
              }]
            }]
          });
          addwin.show();
        }
      }, {
        text: "{% trans 'Delete DRBD Device' %}",
        icon: MEDIA_URL + "/icons2/16x16/actions/remove.png",
        handler: function(self){
          var sm = drbdDevGrid.getSelectionModel();
          if( sm.hasSelection() ){
            var sel = sm.selections.items[0];
            drbd__DrbdDevice.remove( sel.data.id, function(provider, response){
              drbdDevGrid.store.reload();
            } );
          }
        }
      }],
      store: new Ext.data.DirectStore({
        autoLoad: true,
        fields: ['id', 'protocol', 'peeraddress', 'volume', {
          name: 'volumename', mapping: 'volume', convert: function(val, row){ return val.name }
        }],
        directFn: drbd__DrbdDevice.all
      }),
      colModel: new Ext.grid.ColumnModel({
        defaults: {
          sortable: true
        },
        columns: [{
          header: "{% trans 'Volume' %}",
          width: 200,
          dataIndex: "volumename"
        }, {
          header: "{% trans 'Protocol' %}",
          width:     80,
          dataIndex: "protocol"
        }, {
          header: "{% trans 'Peer Address' %}",
          width: 200,
          dataIndex: "peeraddress"
        }]
      })
    }));
    Ext.oa.Drbd__Device_Panel.superclass.initComponent.apply(this, arguments);
  },

  prepareMenuTree: function(tree){
    tree.root.attributes.children[4].children.push({
      text: "{% trans 'DRBD' %}",
      leaf: true,
      icon: MEDIA_URL + '/icons2/22x22/apps/nfs.png',
      panel: this,
      href: '#'
    });
  }
});


window.MainViewModules.push( new Ext.oa.Drbd__Device_Panel() );

// kate: space-indent on; indent-width 2; replace-tabs on;
