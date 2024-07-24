document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('search-form');  // get search form element by id
    const cleanupButton = document.getElementById('cleanup-button');  // get clean up button
    const clearButton = document.getElementById('clear-button');  // get clear button
    const downloadButton = document.getElementById('download-button');

    if (form) {  // check if form element exists
        form.addEventListener('submit', async function(event) {  // add event listener for form submit
            event.preventDefault();  // prevent default form submission
            const formData = new FormData(event.target);  // get form data
            const searchParams = new URLSearchParams(formData);   // create URLSearchParams from form data
            const response = await fetch('/data?' + searchParams.toString());  // fetch data with query parameters
            if (response.ok) {  // check if response is ok
                const data = await response.json();  // parse response data as JSON
                updateChart(data);  // update chart with data
                updateTable(data);  // update table with data
            } else {
                console.error("Failed to retrieve data:", response.statusText);  // log error if data retrieval fails
            }
        });
    }

    cleanupButton.addEventListener('click', async function() {  // add event listener for clean up button
        const cameraId = document.getElementById('camera_id').value;  // get the current camera ID
        const response = await fetch('/cleanup?camera_id=' + cameraId, { method: 'POST' });  // send POST request to /cleanup
        if (response.ok) {
            const data = await response.json();
            updateChart(data);   // update supposed chart that does not work
            updateTable(data);   // update data table
        } else {
            console.error("Failed to clean up data:", response.statusText);
        }
    });

    if (clearButton) {  // check if clear button exists
        clearButton.addEventListener('click', function () {  // add event listener for click of button
            form.reset();  // reset form fields
        });
    }



    downloadButton.addEventListener('click', function() {
        const formData = new FormData(form);
        const searchParams = new URLSearchParams(formData).toString();
        const downloadUrl = `/download_excel?${searchParams}`;

        window.location.href = downloadUrl;
    });

    async function updateChart(data) {  // async function to update chart with data
        const context = document.getElementById('trafficChart').getContext('2d');  // get context of traffic chart canvas
        if (trafficChart) {  // check if chart already exists
            trafficChart.data.labels = data.time;  // update chart labels with time data
            trafficChart.data.datasets[0].data = data.lane_One;  // update chart data for lane one
            trafficChart.data.datasets[1].data = data.lane_Two;  // update chart data for lane two
            trafficChart.data.datasets[2].data = data.lane_Three;  // update chart data for lane three
            trafficChart.update();  // update chart display
        } else {
            trafficChart = new Chart(context, {  // create new chart if it doesn't exist
                type: 'line',  // set chart type to line
                data: {
                    labels: data.time,  // set labels to time data
                    datasets: [
                        {
                            label: 'Lane One',  // label for first dataset
                            data: data.lane_One,  // data for first dataset
                            borderColor: 'red',  // set line color to red
                            fill: false  // do not fill under line
                        },
                        {
                            label: 'Lane Two',  // label for second dataset
                            data: data.lane_Two,  // data for second dataset
                            borderColor: 'blue',  // set line color to blue
                            fill: false  // do not fill under line
                        },
                        {
                            label: 'Lane Three',  // label for third dataset
                            data: data.lane_Three,  // data for third dataset
                            borderColor: 'green',  // set line color to green
                            fill: false  // do not fill under line
                        }
                    ]
                },
                options: {
                    scales: {
                        x: {
                            title: {
                                display: true,  // display x-axis title
                                text: 'Time'  // set x-axis title text
                            }
                        },
                        y: {
                            title: {
                                display: true,  // display y-axis title
                                text: 'Traffic Volume'  // set y-axis title text
                            }
                        }
                    }
                }
            });
        }
    }

    function updateTable(data) {  // function to update table with data
        const tableBody = document.getElementById('data-table-body').querySelector('tbody');  // get table body element
        tableBody.innerHTML = '';  // clear existing table rows
        data.date.forEach((date, index) => {  // iterate over data
            const row = document.createElement('tr');  // create new table row
            row.innerHTML = `
                <td style="width: 16%;">${date}</td> <!-- table cell for date -->
                <td style="width: 16%;">${data.time[index]}</td> <!-- table cell for time -->
                <td style="width: 15%;">${data.dotw[index]}</td> <!-- table cell for day of the week -->
                <td style="width: 15%;">${data.lane_One[index]}</td> <!-- table cell for lane one volume -->
                <td style="width: 15%;">${data.lane_Two[index]}</td> <!-- table cell for lane two volume -->
                <td style="width: 15%;">${data.lane_Three[index]}</td> <!-- table cell for lane three volume -->
            `;
            tableBody.appendChild(row);  // append row to table body
        });
    }
});