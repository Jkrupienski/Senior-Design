import React, { useState } from 'react';  // import react for managing state within the component

// import 'BrowserRouter as Router' to set up routing, (1) 'Route' and (2) 'Switch' (1) def url paths,routes and (2) allows one route rendered at a time
// Link creates navigation links, Redirect to switch user's routes
import { BrowserRouter as Router, Route, Switch, Link, Redirect } from 'react-router-dom';
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
                <nav>  {/* navigation bar with links */}
                    <Link to="/">Home</Link>  {/* link to Home page */}
                    {user && user.role === 'worker' && <Link to="/dashboard">Dashboard</Link>}  {/* render dashboard link if user is logged in as worker */}
                    {user ? <button onClick={logout}>Logout</button> : <Link to="/login">Login</Link>}  {/* render logout button if user logged in, else render login link */}
                </nav>
                <Switch> {/* def routes for application */}
                    <Route path="/" exact component=Home />  {/* route for Home comp, exact path to ensure matches only root URL */}
                    <Route path="/login">
                        {user ? <Redirect to="/" /> : <Login onLogin={login} />}  {/* if user logged in, redirect to homepage else render login component */}
                    </Route>
                    <Route path="/dashboard">  {/* route for Dashboard comp */}
                        {user && user.role === 'worker' ? <Dashboard /> : <Redirect to="/" />}  {/* if user logged in as worker, render Dashboard component, else render Home pg */}
                    </Route>
                </Switch>
            </div>
        </Router>
    );
}
export default App;  // export App component as default export