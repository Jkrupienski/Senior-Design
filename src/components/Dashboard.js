import React, { useEffect, useState } from 'react';
import axios from 'axios';  // for making HTTP reqs
import { Bar } from 'react-chartjs-2';  // to display bar charts

function Dashboard() {  // define dashboard component
    const [data, setData] = useState(null);  // 'data' state and 'setData' func to update data value, init null
    // useState syntax: conts [state, setState] = useState(initialState);
    // 'state' = current state, 'setState' = func to update state, 'initialState' = init value of state
    // search parameters state and func to update, init w default location, date & time (DOTW?)
    const [searchParams, setSearchParams] = useState({
        location: '',  // empty for search
        date: '',  // later have faded text say format to enter? DDMMYYYY
        time: '',  // XX:XX
        //DOTW: '',  // ******** ADD THIS
    })

    useEffect(() => {
        const fetchData = async () => {
            const result = await axios.get('/data');  // GET request to /data endpoint
            setData(result.data);
        };
        fetchData();
    }, []);  // ensures to run only once after initial run

    const handleChange = (e) => {  // update search parameter state when input changes
        setSearchParams({  // func from useState hook to update state
            ...searchParams,  //  spread operator that creates shallow copy '...' of existing state to ensure no properties change that aren't meant to
            [e.target.name]: e.target.value,  // update state based on input name
        });
    };

    const handleSubmit = async (e) => {  // handle search form submission
        e.preventDefault();  // prevent default submission page refresh
        const result = await axios.post('/search-data', searchParams);  // make POST req to '/search-data' endpoint w search params
        setData(result.data);  // update 'data' state with result of request
    };

    const chartData = {  // def data structure for chart using retrieved data
        labels: data ? data.map(d => d.time) : [],  // set labels to time values from data
        datasets: [
            {
                label: 'Traffic Volume',  // label dataset  ** ADD CAM/LOCATION NAME
                data: data ? data.map(d => d.volume) : [],  // set data points to values from traffic volume data
                backgroundColor: 'rgba(75, 192, 192, 0.6)',  // set background color for bars
            },
        ],
    };

    return( // return JSX for component
        <div>
            <h1>Employee Dashboard</h1> {/* website heading*/}
            <form onSubmit={handleSubmit}>
                <label>
                    Location:
                    <input
                        type="text"  // input type as text
                        name="location"  // specify name attribute for IDing input
                        value={searchParams.location}  // bind input to location state
                        onChange={handleChange}  // update location state on input change
                    />
                </label>
                <label>
                    Date:
                    <input
                        type="date"  // input type as date
                        name="date"  // specify name attribute
                        value={searchParams.date}  // bind
                        onChange={handleChange}  // update
                    />
                </label>
                <label>
                    Time:
                    <input
                        type="time"  // input type as time
                        name="time"  // specify name attribute
                        value={searchParams.time}  // bind
                        onChange={handleChange}  // update
                    />
                </label>
                <button type="submit">Search</button>  {/* submit button for form */}
            </form>
            <div style={{ display : 'flex' }}>  {/* flex container for data and chart */}
                <div style={{ flex : 1 }}>  {/* item 1: displaying raw data */}
                    {data ? <pre>{JSON.stringify(data, null, 2)}</pre> : 'Loading ...'}  {/* conditional render retrieved data OR display loading msg */}
                </div>
                <div style={{ flex : 2 }}>
                    {data ? <Bar data={{chartData}} /> : 'Loading ...' }  {/* conditional render bar chart with 'chartData' */}
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
