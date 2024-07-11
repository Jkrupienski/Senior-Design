import React, { useState } from 'react';  // import react for managing state within the component

// import 'BrowserRouter as Router' to set up routing, (1) 'Route' and (2) 'Routes' (1) def url paths,routes and (2) allows one route rendered at a time
// Link creates navigation links, Redirect to switch user's routes
import { BrowserRouter as Router, Route, Routes, Link, Redirect } from 'react-router-dom';
import axios from 'axios';  // import axios for making HTTP requests

import Home from './components/Home';
import Dashboard from './components/Dashboard';
import Login from './components/Login';


function App() { // define main App component
    const [user, setUser] = useState(null);  // declare a state variable 'user' and func 'setUser' to update its value, init to null
    const login = async (username, password) => {  // def async func 'login' to handle user login
        try {
            const response = await axios.post('/login', {username, password});  // make POST req to '/login' endpoint w username and pass
            if (response.data.status === 'success') {  // if login successful
                setUser({username, role: response.data.role});  // update user state w username and role from response
            }

        }catch (error) {
            console.error('Login failed, check credentials.', error);
        }
    };

    const logout = async () => {  // def func 'logout' for user logouts
        await axios.get('/logout');  // make GET req to '/logout' endpoint to log user out
        setUser(null);  // reset user state to null
    }

    return (  // return JSX for the component
        <Router>
            <div>
                <nav>
                    <Link to="/">Home</Link>
                    {user && user.role === 'worker' && <Link to="/dashboard">Dashboard</Link>}
                    {user ? <button onClick={logout}>Logout</button> : <Link to="/login">Login</Link>}
                </nav>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/login" element={user ? <Navigate to="/" /> : <Login onLogin={login} />} />
                        <Route path="/dashboard" element={user && user.role === 'worker' ? <Dashboard /> : <Navigate to="/" />} />
                    </Routes>
            </div>
        </Router>
    );
}
export default App;  // export App component as default export