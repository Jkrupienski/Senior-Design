document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('search-form').addEventListener('submit', async function (event) {
        event.preventDefault();  // default at submission would refresh page, prevent that
        const formData = new FormData(event.target);  // capture form data for use
        const searchParams = new URLSearchParams(formData);  // convert FormData to URL..., create query
        const response = await fetch('/data?' + searchParams.toString());  // fetch and wait for data
        const data = await response.json();  // convert data response to js obj
        updateChart(data);  // update chart with new data, refresh
        document.getElementById('data-container').textContent = JSON.strinify(data, null, 2);  // display data in json format, allows readability
    });

    let trafficChart;  // variable to hold chart instance, 'let' allows variable to be reassigned

    async function fetchData() {  // fetch data, async allows func to use await
        const response = await fetch('/data');  // fetch data
        const data = await response.json();  // ensure data fully parsed and recieved before cont.
        return data;
    }

    async function createChart() {  // create initial chart, uses Chart.js lib
        const data = await fetchData();  // fetch data for charts
        const context = document.getElementById('trafficChart').getContext('2d')
        trafficChart = new Chart(context, {  // new Chart.js instance
            type: 'line',  // line graph
            data: {
                labels: data.time.reverse(),  // reverse time for x-axis label
                datasets: [
                    {
                        label: 'Lane One',  // label lane dataset
                        data: data.lane_One.reverse(),  // data for lane
                        borderColor: 'red',  // line color
                        fill: false  // no fill under the line (maybe change for certain graphs?)
                    },
                    {
                        label: 'Lane Two',  // same as above
                        data: data.lane_Two.reverse(),
                        borderColor: 'blue',
                        fill: false
                    },
                    {
                        label: 'Lane Three',  // same as above
                        data: data.lane_Three.reverse(),
                        borderColor: 'green',
                        fill: false
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,  // display x-axis
                            text: 'Time'  // label x-axis
                        }
                    },
                    y: {
                        title: {
                            display: true,  // display y-axis
                            text: 'Traffic Volume'  // display y-axis
                        }
                    }
                }
            }
        });
    }

    async function updateChart(data) {  // updates chart with new data
        trafficChart.data.labels = data.time.reverse();  // update x-axis with new point in reverse time order
        trafficChart.data.datasets[0].data = data.lane_One.reverse();  // update each lane's data
        trafficChart.data.datasets[1].data = data.lane_Two.reverse();
        trafficChart.data.datasets[2].data = data.lane_Three.reverse();
        trafficChart.update();  // redraw chart with updated data
    }

    setInterval(async function () {  // set up interval to fetch data every 30 sec
        const data = await fetchData();  // fetch data
        updateChart(data);  // update chart with new data
    }, 30000);  // every 30 seconds

    createChart();  // out of a loop to display chart as soon as pg loads

});