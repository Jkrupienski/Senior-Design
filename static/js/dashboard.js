// add an event listener to execute function once DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('search-form'); // get search form element
    const clearButton = document.getElementById('clear-search'); // get clear button
    const cameraTitle = document.getElementById('camera-title'); // get camera title

    if (form) { // check if form element exists
        form.addEventListener('submit', function(event) { // event listener for form submission
            event.preventDefault(); // prevent default form submission
            const cameraId = document.getElementById('camera_id').value; // get value of cam id from input field
            document.getElementById('video-feed').src = `/video_feed?camera_id=${cameraId}`; // set source of vid feed to selected cam id
            updateChart(cameraId); // update chart with selected cam id
            cameraTitle.textContent = `Current Camera: ${cameraId}`; // update text content of camera title element
        });
    }

    if (clearButton) { // check if clear button exists
        clearButton.addEventListener('click', function() { // listener for click of button
            form.reset(); // reset form fields
            updateChart('CAM01_HW_I90'); // update chart with default cam id
            document.getElementById('video-feed').src = `/video_feed?camera_id=CAM01_HW_I90`; // set source of vid feed to default cam id
            cameraTitle.textContent = `Current Camera: CAM01_HW_I90`; // update text content of camera title element
        });
    }

    function submitCounts() { // submit car counts
        const cameraId = document.getElementById('camera_id').value; // get value of cam id input field
        fetch('/stop_counting', { // POST req to stop counting cars
            method: 'POST', // use POST method
            headers: {'Content-Type': 'application/json'}, // set content type to JSON
            body: JSON.stringify({ camera_id: cameraId }), // send cam id as JSON
        }).then(response => {
            if (!response.ok) {
                console.error('Failed to submit car counts.'); // error msg
            }
        });
    }

    setInterval(submitCounts, 60000); // set interval to submit car counts every 60 sec
    window.addEventListener('beforeunload', function() { // listener to submit car counts before page is unloaded  ** not working right now?!!
        submitCounts();
    });

    // CHART ISSUES ********
    async function updateChart(cameraId) { // update chart with given cam id
        const response = await fetch(`/data?camera_id=${cameraId}`); // fetch data of cam id
        if (response.ok) {
            const data = await response.json(); // parse response data as JSON
            createOrUpdateChart(data); // create or update chart with fetched data
        } else {
            console.error("Failed to retrieve data:", response.statusText); // error msg
        }
    }

    let trafficChart; // variable to hold chart instance

    function createOrUpdateChart(data) { // func to create or update chart with given data
        const context = document.getElementById('trafficChart').getContext('2d'); // get context of traffic chart canvas element
        if (trafficChart) { // check if chart already exists
            trafficChart.data.labels = data.time.reverse(); // update chart labels w reversed time data
            trafficChart.data.datasets[0].data = data.lane_One.reverse(); // update chart data
            trafficChart.data.datasets[1].data = data.lane_Two.reverse();
            trafficChart.data.datasets[2].data = data.lane_Three.reverse();
            trafficChart.update(); // update chart display
        } else {
            trafficChart = new Chart(context, { // create new chart if doesn't exist
                type: 'line', // set chart type to line
                data: {
                    labels: data.time.reverse(), // set labels to reversed time data (maybe do not reverse?)
                    datasets: [
                        {
                            label: 'Lane One', // label first lane's dataset
                            data: data.lane_One.reverse(), // data for first lane
                            borderColor: 'red', // set line color to red
                            fill: false // no fill under line
                        },
                        {
                            label: 'Lane Two', // same as above
                            data: data.lane_Two.reverse(),
                            borderColor: 'blue',
                            fill: false
                        },
                        {
                            label: 'Lane Three', // same as above
                            data: data.lane_Three.reverse(),
                            borderColor: 'green',
                            fill: false
                        }
                    ]
                },
                options: {
                    scales: {
                        x: {  // x axis
                            title: {
                                display: true, // display axis title
                                text: 'Time' // label axis
                            }
                        },
                        y: {  // y axis
                            title: {
                                display: true,
                                text: 'Traffic Volume'
                            }
                        }
                    }
                }
            });
        }
    }

    updateChart('CAM01_HW_I90'); // init chart update with default cam id
    setInterval(() => { // set interval to update chart every 30 sec
        const cameraId = document.getElementById('camera_id').value || 'CAM01_HW_I90'; // get current cam id or use default if not set
        updateChart(cameraId); // update chart w current cam id
    }, 30000);
});