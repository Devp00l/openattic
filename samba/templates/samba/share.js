{% load i18n %}

Ext.namespace("Ext.oa");

Ext.oa.Samba__Share_Panel = Ext.extend(Ext.grid.GridPanel, {
  initComponent: function(){
    Ext.apply(this, Ext.apply(this.initialConfig, {
      title: "{% trans 'Samba' %}",
      store: new Ext.data.DirectStore({
        autoLoad: true,
        fields: ['path', 'state', 'available'],
        directFn: samba__Share.all
      }),
      colModel: new Ext.grid.ColumnModel({
        defaults: {
          sortable: true
        },
        columns: [{
          header: "{% trans 'Path' %}",
          width: 200,
          dataIndex: "path"
        }, {
          header: "{% trans 'State' %}",
          width: 50,
          dataIndex: "state"
        }, {
          header: "{% trans 'Available' %}",
          width: 50,
          dataIndex: "available"
        }]
      })
    }));
    Ext.oa.Samba__Share_Panel.superclass.initComponent.apply(this, arguments);
  },

  prepareMenuTree: function(tree){
    tree.root.attributes.children[2].children.push({
      text: "{% trans 'Windows (Samba)' %}",
      leaf: true,
      icon: MEDIA_URL + '/icons2/22x22/apps/samba.png',
      panel: this,
      href: '#'
    });
  }
});


window.MainViewModules.push( new Ext.oa.Samba__Share_Panel() );

// kate: space-indent on; indent-width 2; replace-tabs on;
