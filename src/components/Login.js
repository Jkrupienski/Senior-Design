import React, { useState } from 'react';  // import useState hook from React for managing state within the component

function Login({ onLogin }) {  // define login component taking 'onLogin' as a prop
    // declare state variables username and password with respective setter functions, both init as empty str
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handelSubmit = (e) => {  // define fnc 'handleSubmit' to handle form submission
        e.preventDefault();  // prevent default form submission behavior (would refresh page)
        onLogin(username, password);  // call 'onLogin' func passed as prop w current user and pass
    };

    return (  // return JSX for component
      <form onSubmit={handelSubmit}>  {/* def form element w an onSubmit event handler */}
          <h2>Login</h2>  {/* heading for login pg */}
          <div>  {/* def div for username input */}
              <label>Username</label>  {/* label username input */}
              <input
                  type="text"  {/* declare input type as text */}
                  value={username}  {/* binds input value to username state */}
                  onChange={ (e) => setUsername (e.target.value)}  {/* updates username state on input change */}
                  required  {/* required field */}
              />
          </div>
          <div>  {/* def div for password input */}
              <label>Password</label>
              <input
                type={"password"}  {/* masks input as password type */}
                value={password}
                onChange={ (e) => setPassword(e.target.value)}
                required
              />
          </div>
          <button type="LOGIN">Login</button>  {/* button to submit login info */}
      </form>
    );
}

export default Login;  // export login as defualt export