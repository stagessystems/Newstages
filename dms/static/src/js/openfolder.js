odoo.define('dms.directory', function (require) {
    "use strict";
    
    
        var core = require('web.core');
        var AbstractController = require('web.AbstractController');
    
    AbstractController.include({
        // _onOpenRecord: function (ev) {
        //     console.log("========================")
        //     ev.stopPropagation();
        //     var $target = $(ev.currentTarget);
        //     var data = $target.data();
        //     // console.log("========================"+(ev.data))

            
        //     var record = this.model.get(ev.data.id, {raw: true});
        //     if (this.modelName != "dms.directory"){
        //         console.log("@@@@@@@@@@@@@@@@@@"+this.modelName+"+++++++++"+record.res_id+"------"+ev.data.mode)
        //         this.trigger_up('switch_view', {
        //         view_type: 'form',
        //         res_id: record.res_id,
        //         mode: ev.data.mode || 'readonly',
        //         model: this.modelName,
        //     })
        //     }else{
        //         var domainn = "[('directory_id','=',"+ this.id + ")]"
        //     console.log("========================"+domainn)
        //         this.do_action({
        //             type: 'ir.actions.act_window',
        //             res_model:"dms.file" ,
        //             // domain: domainn ,
        //             res_id: self.id,
        //             views: [[false, 'kanban']],
        //             target: 'current',
        //             name:'kkkkkkk'
        //         },ev.data.context && {additional_context: ev.data.context});
        //     }
            
        // },
        _onOpenRecord: function (event) {
    
                if (this.modelName === "dms.directory"){
                    console.log("==============new ")
                    event.stopPropagation();
                var record = this.model.get(event.data.id, {raw: true});
                var self = this
                this._rpc({
                        model : 'dms.directory',
                        method: 'search_read',
                        domain : [['id','=', record.res_id]],
                        fields : ['id','name']
                    })
                    .then(function (result) {
                        var name = _.map(result, function(record) {
                            return record['name'];
                        });
                        var domainn = "[('directory_id','=',"+ result[0]['id'] + ")]"
                        var ctx = "{'default_directory_id' :"+result[0]['id']+"}"
                        // console.log(ctx)
                        // console.log(";;;;;;;;;;;;;;;;;;;;;;")
                        self.do_action({
                        type: 'ir.actions.act_window',
                        res_model:"dms.file" ,
                        domain: domainn ,
                        //res_id: self.id,
                        views: [[false, 'kanban'],[false, 'list'],[false, 'form']],
                        target: 'current',
                        name:name[0],
                        context : ctx

                    })
    
    
                    })
                
                }else if(this.modelName === "dms.storage"){
                    console.log("==============new ")
                    event.stopPropagation();
                var record = this.model.get(event.data.id, {raw: true});
                var self = this
                this._rpc({
                        model : 'dms.storage',
                        method: 'search_read',
                        domain : [['id','=', record.res_id]],
                        fields : ['id','name']
                    })
                    .then(function (result) {
                        var name = _.map(result, function(record) {
                            return record['name'];
                        });
                        var domainn = "[('storage_id','=',"+ result[0]['id'] + ")]"
                        var ctx = "{'default_storage_id' :"+result[0]['id']+",'default_is_root_directory': 1}"
                        console.log(ctx)
                        // console.log(";;;;;;;;;;;;;;;;;;;;;;")
                        self.do_action({
                        type: 'ir.actions.act_window',
                        res_model:"dms.directory" ,
                        domain: domainn ,
                        //res_id: self.id,
                        views: [[false, 'kanban'],[false, 'list'],[false, 'form']],
                        target: 'current',
                        name:name[0],
                        context : ctx

                    })
    
    
                    })

                }
                else{
                    console.log("==============new ")
                    this._super.apply(this,arguments);
                }
            },
        });
    
    
    });
