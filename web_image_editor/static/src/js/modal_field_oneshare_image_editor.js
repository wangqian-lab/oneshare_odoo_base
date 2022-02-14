odoo.define('oneshare.modal_image_editor', function (require) {
    'use strict';

    const AbstractField = require('web.AbstractField');
    const fieldRegistry = require('web.field_registry');
    const basic_fields = require('web.basic_fields');
    const FieldBinaryImage = basic_fields.FieldBinaryImage;
    var utils = require('web.utils');

    var core = require('web.core');

    var _lt = core._lt;

    var _getImageUrl = FieldBinaryImage.prototype._getImageUrl;

    var file_type_magic_word = FieldBinaryImage.prototype.file_type_magic_word;

    var ImageEditor = AbstractField.extend({

        description: _lt("Image Editor"),
        template: 'OneshareImageEditor',
        placeholder: "/web/static/src/img/placeholder.png",

        _render: function () {
            var self = this;
            var url = this.placeholder;
            if (this.value) {
                if (!utils.is_bin_size(this.value)) {
                    // Use magic-word technique for detecting image type
                    url = 'data:image/' + (file_type_magic_word[this.value[0]] || 'png') + ';base64,' + this.value;
                } else {
                    var field = this.nodeOptions.preview_image || this.name;
                    var unique = this.recordData.__last_update;
                    url = _getImageUrl(this.model, this.res_id, field, unique);
                }
            }
            this.$el.find('#img_block').append('<div id="img_container" class="img-container">' +
                '<img id="img" class="img" src="' + url + '" alt=""/>' +
                '</div>');

            return this._super.apply(this, arguments);
        },


    });
    fieldRegistry.add('oneshare_image_editor', ImageEditor);
    return ImageEditor;
});

