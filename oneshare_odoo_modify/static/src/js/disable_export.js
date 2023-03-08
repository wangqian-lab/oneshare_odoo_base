odoo.define("oneshare_odoo_modify.disable_export", function (require) {
  "use strict";

  var ListController = require("web.ListController");
  var ListView = require("web.ListView");
  var viewRegistry = require("web.view_registry");

  var DisableExportController = ListController.extend({
    _getActionMenuItems: function (state) {
      this.isExportEnable = false; // 一定不能导出
      return this._super(...arguments);
    },
  });

  var DisableExportListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
      Controller: DisableExportController,
    }),
  });

  viewRegistry.add("onesphere_disable_export", DisableExportListView);
});
