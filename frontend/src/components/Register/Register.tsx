import React from "react";
import { useForm } from "react-hook-form";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Register() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm();
    const navigate = useNavigate();
    const onSubmit = async (data: any) => {

        if (data.password !== data.retypePassword) {
            alert("Passwords do not match!");
            return;
        }
        const userData = {
            phone: data.phone,
            email: data.email,
            password: data.password,
        };
            try {
            const response = await axios.post("http://localhost:8000/register", userData);

            console.log("Backend Response:", response.data);
            alert(response.data.message); 
            
            navigate("/login"); 
            
        } catch (error: any) {
            if (error.response) {
                console.error("Backend Error:", error.response.data);
                alert("Error: " + error.response.data.detail);
            } else {
                console.error("Connection Error:", error.message);
                alert("Cannot connect to server. Is Uvicorn running?");
            }
        }
        
    };

    return (
        <>
            <h2>Register</h2>

            <form className="App" onSubmit={handleSubmit(onSubmit)}>
                <input
                    type="email"
                    {...register("email", { required: true })}
                    placeholder="Email"
                />
                {errors.email && <span style={{ color: "red" }}>*Email* is mandatory</span>}

                <input
                    type="text"
                    {...register("phone", { required: true })}
                    placeholder="Phone Number"
                />
                {errors.phone && <span style={{ color: "red" }}>*Phone Number* is mandatory</span>}


                <input
                    type="password"
                    {...register("password", { required: true })}
                    placeholder="Password"
                />
                {errors.password && <span style={{ color: "red" }}>*Password* is mandatory</span>}
                <input
                    type="password"
                    {...register("retypePassword", { required: true })}
                    placeholder="Retype Password"
                />
                {errors.retypePassword && <span style={{ color: "red" }}>*Retype Password* is mandatory</span>}

                <input value="Create Account" type="submit" style={{ backgroundColor: "blueviolet" }} />
                <p>Already have an account? <a href="/login">Login</a></p>
            </form>
        </>
    );
}

export default Register;