import { ReactCreditCard } from "@repay/react-credit-card";
import type { FOCUS_TYPE } from "@repay/react-credit-card/dist/ReactCreditCard";
import React from "react";
import "@repay/react-credit-card/dist/react-credit-card.css";
import axios from "axios";
import { useNavigate } from "react-router-dom";
const styles: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",

  gap: "10px",
  padding: "20px",
};
const fieldsetRowStyle: React.CSSProperties = {
  width: "100%",
  maxWidth: "400px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  border: "none",
  padding: "5px 0"
};


export default function AddCard() {
  const [values, setValues] = React.useState({
    name: "",
    number: "",
    expiration: "",
    cvc: ""
  });
  
  const navigate = useNavigate();
  const handleChange = React.useCallback(
    event => {
      const { name, value } = event.target;
      setValues(v => ({ ...v, [name]: value }));
    },
    [setValues]
  );

  const [focused, setFocus] = React.useState<FOCUS_TYPE | undefined>(undefined);
  const handleFocus = React.useCallback(
    event => setFocus(event.target.name as FOCUS_TYPE),
    [setFocus]
  );
  const handleBlur = React.useCallback(() => setFocus(undefined), [setFocus]);
  function addCard(e:React.FormEvent) {
    if (e) e.preventDefault();
    if (values.name == "" || values.number == "" || values.expiration == "" || values.cvc == "") {
      alert("Please fill in all fields");
      return;
    }
    if (values.number.length < 16 || !/^[0-9]+$/.test(values.number)) {
      alert("Card number must be 16 digits");
      return;
    }
    if (values.cvc.length < 3) {
      alert("CVC must be 3 digits");
      return;
    }
    if (!/^(0[1-9]|1[0-2])\/?([0-9]{2})$/.test(values.expiration)) {
      alert("Expiration date must be in MM/YY format");
      return;
    }
    axios.post("http://localhost:8000/card", values,
      {
        headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      }).then(() => {
        navigate("/")
      }).catch((error) => {
        alert("Error adding card: " + error.response.data.message);
      });
    
  }
  return (
    <form style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }} >
      <div style={styles}>
        <fieldset style={fieldsetRowStyle}>
          <label>Name on card </label>
          <input
            name="name"
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            value={values.name}
          />
        </fieldset>
        <fieldset style={fieldsetRowStyle}>
          <label>Card Number </label>
          <input
            name="number"
            onChange={handleChange}
            onFocus={handleFocus}
            maxLength={16}
            onBlur={handleBlur}
            value={values.number}
          />
        </fieldset>
        <fieldset style={fieldsetRowStyle}>
          <label>Expiration </label>
          <input
            name="expiration"
            placeholder="MM/YY"
            onChange={handleChange}
            onFocus={handleFocus}
            maxLength={5}

            onBlur={handleBlur}
            value={values.expiration}
          />
        </fieldset>
        <fieldset style={fieldsetRowStyle}>
          <label>CVC </label>
          <input
            name="cvc"
            maxLength={3}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            value={values.cvc}
          />
        </fieldset>
        <ReactCreditCard {...values} focused={focused} />
      </div>
      <button onClick={addCard} type="button">Add Card</button>
    </form>
  );
}