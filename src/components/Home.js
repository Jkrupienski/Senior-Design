import React, { useEffect, useState } from 'react';  // import hooks
import axios from 'axios';  // import axios for making HTTP requests

function Home() {  // define Home component
    const [data, setData] = useState(null);  // declare state variable 'data' and a func 'setData' to update values, init to null
    useEffect( () => {  // use the useEffect hook to perform side effects in func components

        const fetchData = async () => {  // def async func to fetch data from the server
            const result = await axios.get('/public-data');  // make GET req to the '/public-data' end pt
            setData(result.data);  // update 'data' state w result of request
        };
        fetchData();  // call fetchData func to init data fetching
    }, []);  // empty array [] ensures effect only runs once after initial render

    return (  // return jsx
        <div>
            <h1>Public Data</h1>  {/* public data heading */}
            {/* if 'data' is not null, render data as JSON string, else display loading msg */}
            {data ? <pre>{JSON.stringify(data,null,2)}</pre> : 'Loading...'}
        </div>
    );
}

export default Home;  // export home as default export