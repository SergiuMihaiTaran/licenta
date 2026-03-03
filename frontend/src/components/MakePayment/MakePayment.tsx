import axios from "axios";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import "./MakePayment.css";

import { useNavigate } from "react-router-dom";
function MakePayment() {
    const navigate = useNavigate();
    const [details, setDetails] = useState({
        amount: 0,
        iban: "",
        type: ""
    });
    function sendPayment() {
        if (details.iban.length < 16 || details.amount <= 0 || details.type === "") {
            alert("Please fill in all fields correctly");
            console.log(details);
            return;
        }
        axios.post("http://localhost:8000/payment", details, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("token")}`,
                "Content-Type": "application/json",
            },
        }).then(() => {
            navigate("/");
        }).catch((error) => {
            alert("Error making payment: " + error.response.data.detail);
        });
    }
    return (
        <div className="make-payment-container">
            <h2>Make Payment</h2>
            <form className="make-payment-form" onSubmit={(e) => {
                e.preventDefault();
                sendPayment()

            }}>
                <input onChange={(e) => setDetails({ ...details, iban: e.target.value })}
                    type="text" placeholder="Recipient IBAN" />
                <input onChange={(e) => setDetails({ ...details, amount: parseFloat(e.target.value) || 0 })}
                    type="number" step="0.01" placeholder="Amount" />
                <label htmlFor="types-select">Payment Type:</label>
                <select
                    value={details.type}
                    onChange={(e) => setDetails({ ...details, type: e.target.value })}
                    name="Types"
                    id="types-select">
                    <option disabled value="">Type</option>
                    <option value="Food & Dining">Food & Dining</option>
                    <option value="Shopping & Retail">Shopping & Retail</option>
                    <option value="Utilities & Services">Utilities & Services</option>
                    <option value="Entertainment & Travel">Entertainment & Travel</option>
                    <option value="Transportation">Transportation</option>
                    <option value="Health & Wellness">Health & Wellness</option>
                    <option value="Home & Garden">Home & Garden</option>
                    <option value="Electronics & Tech">Electronics & Tech</option>
                    <option value="Industrial & Business">Industrial & Business</option>
                    <option value="Other">Other</option>
                </select>
                <button type="submit">Pay Now</button>
            </form>
        </div>
    );
}
export default MakePayment;