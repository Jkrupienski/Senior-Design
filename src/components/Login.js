import React, { useState } from 'react';  // import useState hook from React for managing state within the component

function Login({ onLogin }) {  // define login component taking 'onLogin' as a prop
    // declare state variables username and password with respective setter functions, both init as empty str
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {  // define fnc 'handleSubmit' to handle form submission
        e.preventDefault();  // prevent default form submission behavior (would refresh page)
        onLogin(username, password);  // call 'onLogin' func passed as prop w current user and pass
    };

    return (  // return JSX for component
        <form onSubmit={handleSubmit}>
            <h2>Login</h2>
            <div>
                <label>Username</label>
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
            </div>
            <div>
                <label>Password</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </div>
            <button type="submit">Login</button>
        </form>
    );
}

export default Login;  // export login as default export
