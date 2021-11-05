odoo.define('oneshare.field_image_editor', function (require) {
    "use strict";
    var fieldRegistry = require('web.field_registry');
    var FieldBinaryImage = fieldRegistry.get('image');
    var core = require('web.core');

    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;


    var FieldBinaryImageEditor = FieldBinaryImage.extend({

        description: _lt("Image Editor"),
        template: 'FieldBinaryImageEditor',

        events: _.extend({}, FieldBinaryImage.prototype.events, {
            'click .o_form_binary_image_darkroom_modal': '_onOpenEditorModalClick',
        }),

        _onOpenEditorModalClick: function (ev) {
            var self = this;
            var activeModel = self.model;
            var activeRecordId = self.res_id;
            var activeField = self.name;
            var context = {
                active_model: activeModel,
                active_record_id: activeRecordId,
                active_field: activeField,
            };
            var getViewId = this._rpc({
                model: 'oneshare.modal',
                method: 'get_image_editor_action',
                args: [[]],
                context: context,
            }).then(function (res) {
                var modalAction = {
                    type: 'ir.actions.act_window',
                    res_model: 'oneshare.modal',
                    name: 'Image Editor',
                    views: [[res, 'form']],
                    target: 'new',
                    context: context,
                };
                self.do_action(modalAction);
            });
        },

    });
    fieldRegistry.add('imageEditor', FieldBinaryImageEditor);

})
;