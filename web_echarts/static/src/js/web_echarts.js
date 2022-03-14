odoo.define('onesphere.web_echarts', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var _lt = core._lt;


    var EChartWidget = AbstractField.extend({
        _render: function () {
//            var value = this.get('value');
            var value = this.value;
            var isJson = false;
            try {
                var val = JSON.parse(value);
                isJson = true;
            } catch (e) {
                this.$el.html(value);
            }
            if (!isJson) {
                return;
            }
            var chart = echarts.init(this.el, null, {
                width: this.nodeOptions.width || 950,
                height: this.nodeOptions.height || 600
            });
            var xLabel = this.nodeOptions.xLabel || 'cur_w';
            var yLabel = this.nodeOptions.yLabel || 'cur_m';
            var series = [];
            var names = [];
            for (var v in val) {
                if (val[v]) {
                    series.push({
                        data: this.genData(val[v][xLabel], val[v][yLabel]),
                        type: 'line',
                        name: val[v]['name'],
                        symbol: 'none',
                        markLine: {
                            data: [
                                {type: 'min', name: _lt('Min')},
                                {type: 'max', name: _lt('Max')}
                            ]
                        },
                        smooth: true,
                    });
                    names.push(val[v]['name']);
                }
            }
            var option = {
                title: {
                    text: ''
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {},
                yAxis: {},
                dataZoom: [
                    {
                        type: 'slider',
                        xAxisIndex: 0,
                        filterMode: 'empty'
                    },
                    {
                        type: 'slider',
                        yAxisIndex: 0,
                        filterMode: 'empty'
                    },
                    {
                        type: 'inside',
                        xAxisIndex: 0,
                        filterMode: 'empty'
                    },
                    {
                        type: 'inside',
                        yAxisIndex: 0,
                        filterMode: 'empty'
                    }
                ],
                legend: {
                    type: 'scroll',
                    left: 10,
                    top: 0,
                    data: names
                },
                series
            };
            chart.setOption(option);
            chart.resize();
        },

        genData: function (xData, yData) {
            var data = [];
            for (var x in xData) {
                data.push([xData[x], yData[x]])
            }
            return data;
        }
    });
    fieldRegistry.add('web_echarts', EChartWidget);
    return {
        EChartWidget: EChartWidget
    };
});