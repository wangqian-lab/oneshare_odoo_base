# -*- coding: utf-8 -*-
import uuid

from odoo import models, fields, api, _


class Channel(models.Model):
    """ A channel is a container of slides. """
    _inherit = 'slide.channel'

    nbr_iframe = fields.Integer("Iframes", compute='_compute_slides_statistics', store=True)


class Slide(models.Model):
    _inherit = 'slide.slide'

    slide_type = fields.Selection(selection_add=[("iframe", _("IFRAME"))], ondelete={"iframe": "set default"})

    nbr_iframe = fields.Integer("Number of Iframes", compute='_compute_slides_statistics', store=True)

    def _find_document_data_from_url(self, url):
        if self.slide_type == 'iframe':
            return ('iframe', self.id)
        else:
            return super(Slide, self)._find_document_data_from_url(url)

    def _parse_iframe_document(self, document_id, only_preview_fields):
        values = {
            'slide_type': 'iframe',
            'document_id': uuid.uuid4().hex,
            'image_1920': False,
            'mime_type': False,
        }
        return {'values': values}

    @api.depends()
    def _compute_embed_code(self):
        super(Slide, self)._compute_embed_code()
        for rec in self:
            if rec.slide_type == 'iframe':
                rec.embed_code = rec.url
                if hasattr(rec, 'embed_code_external'):
                    rec.embed_code_external = rec.url
