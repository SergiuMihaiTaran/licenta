import axios from "axios";
import React from "react";
import { useForm } from "react-hook-form";
import "./Login.css";
import { useNavigate } from "react-router-dom";
function Login() {
    const navigate = useNavigate();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm();

    const onSubmit = (data: any) => {
        axios.post("http://localhost:8000/login", data)
            .then((response) => {
                console.log("Backend Response:", response.data);
                localStorage.setItem("token", response.data.token);
                navigate("/");

            });
    };

    return (
        <>
                <h2>Login</h2>

                <form className="App" onSubmit={handleSubmit(onSubmit)}>
                    
                    <input
                        type="text"
                        {...register("identifier", { required: true })}
                        placeholder="Email or Phone"
                    />
                    {errors.identifier && <span style={{ color: "red" }}>*Phone or Email* is mandatory</span>}
                    <input
                        type="password"
                        {...register("password", { required: true })}
                        placeholder="Password"
                    />
                    {errors.password && <span style={{ color: "red" }}>*Password* is mandatory</span>}
                    <input value="Login" className="submit" type="submit" />
                    <p>Don't have an account? <a href="/register">Register</a></p>
                </form>

        </>

    );
}

export default Login;