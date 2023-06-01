odoo.define("website_slides.oneshare_website_slide_iframe", function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var FullScreen = require('website_slides.fullscreen');

    FullScreen.include({
        xmlDependencies: (FullScreen.prototype.xmlDependencies || []).concat(
            ["/oneshare_website_slide_iframe/static/src/xml/website_slides_fullscreen.xml"]
        ),
        _renderSlide: function () {
            var def = this._super.apply(this, arguments);
            var slide = this.get('slide');
            var $content = this.$('.o_wslides_fs_content');
            if (slide.type === 'iframe') {
                $content.html(QWeb.render('website.slides.fullscreen.content.iframe', {widget: this}));
            }
            return Promise.all([def]);
        }
    });

});