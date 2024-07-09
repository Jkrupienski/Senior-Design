import React, { useEffect, useState } from 'react';
import axios from 'axios';  // for making HTTP reqs
import { Bar } from 'react-chartjs-2';  // to display bar charts

function Dashboard() {  // define dashboard component
    const [data, setData] = useState(null);  // 'data' state and 'setData' func to update data value, init null
    // search parameters state and func to update, init w default date & time
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
        setSearchParams({

        })
    }
}
