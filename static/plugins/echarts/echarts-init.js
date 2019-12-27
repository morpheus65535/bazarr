// ============================================================== 
// Bar chart option
// ============================================================== 
var myChart = echarts.init(document.getElementById('bar-chart'));

// specify chart configuration item and data
option = {
    tooltip: {
        trigger: 'axis'
    },
    legend: {
        data: ['Site A', 'Site B']
    },
    toolbox: {
        show: true,
        feature: {

            magicType: { show: true, type: ['line', 'bar'] },
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    color: ["#55ce63", "#009efb"],
    calculable: true,
    xAxis: [{
        type: 'category',
        data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
    }],
    yAxis: [{
        type: 'value'
    }],
    series: [{
            name: 'Site A',
            type: 'bar',
            data: [2.0, 4.9, 7.0, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20.0, 6.4, 3.3],
            markPoint: {
                data: [
                    { type: 'max', name: 'Max' },
                    { type: 'min', name: 'Min' }
                ]
            },
            markLine: {
                data: [
                    { type: 'average', name: 'Average' }
                ]
            }
        },
        {
            name: 'Site B',
            type: 'bar',
            data: [2.6, 5.9, 9.0, 26.4, 28.7, 70.7, 175.6, 182.2, 48.7, 18.8, 6.0, 2.3],
            markPoint: {
                data: [
                    { name: 'The highest year', value: 182.2, xAxis: 7, yAxis: 183, symbolSize: 18 },
                    { name: 'Year minimum', value: 2.3, xAxis: 11, yAxis: 3 }
                ]
            },
            markLine: {
                data: [
                    { type: 'average', name: 'Average' }
                ]
            }
        }
    ]
};


// use configuration item and data specified to show chart
myChart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            myChart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});

// ============================================================== 
// Line chart
// ============================================================== 
var dom = document.getElementById("main");
var mytempChart = echarts.init(dom);
var app = {};
option = null;
option = {

    tooltip: {
        trigger: 'axis'
    },
    legend: {
        data: ['max temp', 'min temp']
    },
    toolbox: {
        show: true,
        feature: {
            magicType: { show: true, type: ['line', 'bar'] },
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    color: ["#55ce63", "#009efb"],
    calculable: true,
    xAxis: [{
        type: 'category',

        boundaryGap: false,
        data: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    }],
    yAxis: [{
        type: 'value',
        axisLabel: {
            formatter: '{value} °C'
        }
    }],

    series: [{
            name: 'max temp',
            type: 'line',
            color: ['#000'],
            data: [11, 11, 15, 13, 12, 13, 10],
            markPoint: {
                data: [
                    { type: 'max', name: 'Max' },
                    { type: 'min', name: 'Min' }
                ]
            },
            itemStyle: {
                normal: {
                    lineStyle: {
                        shadowColor: 'rgba(0,0,0,0.3)',
                        shadowBlur: 10,
                        shadowOffsetX: 8,
                        shadowOffsetY: 8
                    }
                }
            },
            markLine: {
                data: [
                    { type: 'average', name: 'Average' }
                ]
            }
        },
        {
            name: 'min temp',
            type: 'line',
            data: [1, -2, 2, 5, 3, 2, 0],
            markPoint: {
                data: [
                    { name: 'Week minimum', value: -2, xAxis: 1, yAxis: -1.5 }
                ]
            },
            itemStyle: {
                normal: {
                    lineStyle: {
                        shadowColor: 'rgba(0,0,0,0.3)',
                        shadowBlur: 10,
                        shadowOffsetX: 8,
                        shadowOffsetY: 8
                    }
                }
            },
            markLine: {
                data: [
                    { type: 'average', name: 'Average' }
                ]
            }
        }
    ]
};

if (option && typeof option === "object") {
    mytempChart.setOption(option, true), $(function() {
        function resize() {
            setTimeout(function() {
                mytempChart.resize()
            }, 100)
        }
        $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
    });
}

// ============================================================== 
// Pie chart option
// ============================================================== 
var pieChart = echarts.init(document.getElementById('pie-chart'));

// specify chart configuration item and data
option = {

    tooltip: {
        trigger: 'item',
        formatter: "{a} <br/>{b} : {c} ({d}%)"
    },
    legend: {
        x: 'center',
        y: 'bottom',
        data: ['rose1', 'rose2', 'rose3', 'rose4', 'rose5', 'rose6', 'rose7', 'rose8']
    },
    toolbox: {
        show: true,
        feature: {

            dataView: { show: true, readOnly: false },
            magicType: {
                show: true,
                type: ['pie', 'funnel']
            },
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    color: ["#f62d51", "#dddddd", "#ffbc34", "#7460ee", "#009efb", "#2f3d4a", "#90a4ae", "#55ce63"],
    calculable: true,
    series: [{
            name: 'Radius mode',
            type: 'pie',
            radius: [20, 110],
            center: ['25%', 200],
            roseType: 'radius',
            width: '40%', // for funnel
            max: 40, // for funnel
            itemStyle: {
                normal: {
                    label: {
                        show: false
                    },
                    labelLine: {
                        show: false
                    }
                },
                emphasis: {
                    label: {
                        show: true
                    },
                    labelLine: {
                        show: true
                    }
                }
            },
            data: [
                { value: 10, name: 'rose1' },
                { value: 5, name: 'rose2' },
                { value: 15, name: 'rose3' },
                { value: 25, name: 'rose4' },
                { value: 20, name: 'rose5' },
                { value: 35, name: 'rose6' },
                { value: 30, name: 'rose7' },
                { value: 40, name: 'rose8' }
            ]
        },
        {
            name: 'Area mode',
            type: 'pie',
            radius: [30, 110],
            center: ['75%', 200],
            roseType: 'area',
            x: '50%', // for funnel
            max: 40, // for funnel
            sort: 'ascending', // for funnel
            data: [
                { value: 10, name: 'rose1' },
                { value: 5, name: 'rose2' },
                { value: 15, name: 'rose3' },
                { value: 25, name: 'rose4' },
                { value: 20, name: 'rose5' },
                { value: 35, name: 'rose6' },
                { value: 30, name: 'rose7' },
                { value: 40, name: 'rose8' }
            ]
        }
    ]
};



// use configuration item and data specified to show chart
pieChart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            pieChart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});

// ============================================================== 
// Radar chart option
// ============================================================== 
var radarChart = echarts.init(document.getElementById('radar-chart'));

// specify chart configuration item and data

option = {

    tooltip: {
        trigger: 'axis'
    },
    legend: {
        orient: 'vertical',
        x: 'right',
        y: 'bottom',
        data: ['Allocated Budget', 'Actual Spending']
    },
    toolbox: {
        show: true,
        feature: {
            dataView: { show: true, readOnly: false },
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    polar: [{
        indicator: [
            { text: 'sales', max: 6000 },
            { text: 'Administration', max: 16000 },
            { text: 'Information Techology', max: 30000 },
            { text: 'Customer Support', max: 38000 },
            { text: 'Development', max: 52000 },
            { text: 'Marketing', max: 25000 }
        ]
    }],
    color: ["#55ce63", "#009efb"],
    calculable: true,
    series: [{
        name: 'Budget vs spending',
        type: 'radar',
        data: [{
                value: [4300, 10000, 28000, 35000, 50000, 19000],
                name: 'Allocated Budget'
            },
            {
                value: [5000, 14000, 28000, 31000, 42000, 21000],
                name: 'Actual Spending'
            }
        ]
    }]
};




// use configuration item and data specified to show chart
radarChart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            radarChart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});

// ============================================================== 
// doughnut chart option
// ============================================================== 
var doughnutChart = echarts.init(document.getElementById('doughnut-chart'));

// specify chart configuration item and data

option = {
    tooltip: {
        trigger: 'item',
        formatter: "{a} <br/>{b} : {c} ({d}%)"
    },
    legend: {
        orient: 'vertical',
        x: 'left',
        data: ['Item A', 'Item B', 'Item C', 'Item D', 'Item E']
    },
    toolbox: {
        show: true,
        feature: {
            dataView: { show: true, readOnly: false },
            magicType: {
                show: true,
                type: ['pie', 'funnel'],
                option: {
                    funnel: {
                        x: '25%',
                        width: '50%',
                        funnelAlign: 'center',
                        max: 1548
                    }
                }
            },
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    color: ["#f62d51", "#009efb", "#55ce63", "#ffbc34", "#2f3d4a"],
    calculable: true,
    series: [{
        name: 'Source',
        type: 'pie',
        radius: ['80%', '90%'],
        itemStyle: {
            normal: {
                label: {
                    show: false
                },
                labelLine: {
                    show: false
                }
            },
            emphasis: {
                label: {
                    show: true,
                    position: 'center',
                    textStyle: {
                        fontSize: '30',
                        fontWeight: 'bold'
                    }
                }
            }
        },
        data: [
            { value: 335, name: 'Item A' },
            { value: 310, name: 'Item B' },
            { value: 234, name: 'Item C' },
            { value: 135, name: 'Item D' },
            { value: 1548, name: 'Item E' }
        ]
    }]
};



// use configuration item and data specified to show chart
doughnutChart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            doughnutChart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});

// ============================================================== 
// Gauge chart option
// ============================================================== 
var gaugeChart = echarts.init(document.getElementById('gauge-chart'));

// specify chart configuration item and data
option = {
    tooltip: {
        formatter: "{a} <br/>{b} : {c}%"
    },
    toolbox: {
        show: true,
        feature: {
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },

    series: [{
        name: 'Speed',
        type: 'gauge',
        detail: { formatter: '{value}%' },
        data: [{ value: 50, name: 'Speed' }],
        axisLine: { // 坐标轴线
            lineStyle: { // 属性lineStyle控制线条样式
                color: [
                    [0.2, '#55ce63'],
                    [0.8, '#009efb'],
                    [1, '#f62d51']
                ],

            }
        },

    }]
};
timeTicket = setInterval(function() {
    option.series[0].data[0].value = (Math.random() * 100).toFixed(2) - 0;
    gaugeChart.setOption(option, true);
}, 2000);


// use configuration item and data specified to show chart
gaugeChart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            gaugeChart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});

// ============================================================== 
// Radar chart option
// ============================================================== 
var gauge2Chart = echarts.init(document.getElementById('gauge2-chart'));

// specify chart configuration item and data
option = {
    tooltip: {
        formatter: "{a} <br/>{b} : {c}%"
    },
    toolbox: {
        show: true,
        feature: {
            restore: { show: true },
            saveAsImage: { show: true }
        }
    },
    series: [{
        name: 'Market',
        type: 'gauge',
        splitNumber: 10, // 分割段数，默认为5
        axisLine: { // 坐标轴线
            lineStyle: { // 属性lineStyle控制线条样式
                color: [
                    [0.2, '#55ce63'],
                    [0.8, '#009efb'],
                    [1, '#f62d51']
                ],
                width: 8
            }
        },
        axisTick: { // 坐标轴小标记
            splitNumber: 10, // 每份split细分多少段
            length: 12, // 属性length控制线长
            lineStyle: { // 属性lineStyle控制线条样式
                color: 'auto'
            }
        },
        axisLabel: { // 坐标轴文本标签，详见axis.axisLabel
            textStyle: { // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                color: 'auto'
            }
        },
        splitLine: { // 分隔线
            show: true, // 默认显示，属性show控制显示与否
            length: 30, // 属性length控制线长
            lineStyle: { // 属性lineStyle（详见lineStyle）控制线条样式
                color: 'auto'
            }
        },
        pointer: {
            width: 5
        },
        title: {
            show: true,
            offsetCenter: [0, '-40%'], // x, y，单位px
            textStyle: { // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                fontWeight: 'bolder'
            }
        },
        detail: {
            formatter: '{value}%',
            textStyle: { // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                color: 'auto',
                fontWeight: 'bolder'
            }
        },
        data: [{ value: 50, name: 'Rate' }]
    }]
};

clearInterval(timeTicket);
timeTicket = setInterval(function() {
    option.series[0].data[0].value = (Math.random() * 100).toFixed(2) - 0;
    gauge2Chart.setOption(option, true);
}, 2000)


// use configuration item and data specified to show chart
gauge2Chart.setOption(option, true), $(function() {
    function resize() {
        setTimeout(function() {
            gauge2Chart.resize()
        }, 100)
    }
    $(window).on("resize", resize), $(".sidebartoggler").on("click", resize)
});