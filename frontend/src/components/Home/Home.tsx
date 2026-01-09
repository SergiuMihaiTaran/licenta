import { ReactCreditCard } from "@repay/react-credit-card";
import React, { useEffect, useLayoutEffect, useState } from "react";
import "@repay/react-credit-card/dist/react-credit-card.css";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { ClipLoader } from "react-spinners";
import "./Home.css";
import { set } from "react-hook-form";
type Focused = "number" | "cvc" | "name" | "expiration" | undefined;
function Home() {
  const navigate = useNavigate();
  const apiUrlMinimalCardInfo = "http://localhost:8000/card/mininmal_info";
  const apuiUrlFullCardInfo = "http://localhost:8000/card";
  const [showAllDetails, setShowAllDetails] = useState(false);
  const [focusedField, setFocusedField] = useState("undefined" as Focused);
  const [values, setValues] = useState({
    name: "",
    number: "",
    expiration: "",
    balance: 0,
    cvc: "",
    
  });
  // function fetchAllCardData() {
  //   axios.get("http://localhost:8000/card/full_info", {
  //     headers: {
  function fetchMinimalCardData() {
    const apiUrl = showAllDetails ? apuiUrlFullCardInfo : apiUrlMinimalCardInfo;
    axios.get(apiUrl, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        "Content-Type": "application/json",
      },
    })
      .then((response) => {

        const data = response.data;
        if (!showAllDetails)
          setValues({
            ...values,
            balance: data.balance,
            name: data.name,
            cvc: "",
            expiration: "",
            number: `************${data.number}`
            
          });
        else {
          setValues({
            name: data.name,
            number: data.number,
            expiration: data.expiration,
            balance: parseFloat(data.balance),
            cvc: data.cvc
            
          });
        }
        setLoading(false);

      })
      .catch((err) => {
        console.error("Error fetching card:", err);
        setLoading(false);
      });
  }
  const [loading, setLoading] = useState(true);
  useLayoutEffect(fetchMinimalCardData,
    [showAllDetails]);
  const handleCardClick = () => {
    if (focusedField === "cvc") {
      setFocusedField(undefined);
    } else {
      setFocusedField("cvc");
    }
  };
  if (loading) {
    return (
      <div className="loading" >
        <ClipLoader color="#36d7b7" size={50} />
      </div>
    );
  }
  return (
    console.log("rerendering Home"),
    <div className="card-preview">
      <div className="card">

        {values.name &&
          <div className="card-details">
            <div className="onlyCard" onClick={handleCardClick} >
            <ReactCreditCard {...values}
            type="default"
            focused={focusedField} />
            </div>
            <h3>Balance: {values.balance}$</h3>
            <button onClick={(makePayment)}>Make a payment</button>
            <button onClick={(showCardDetails)}> {showAllDetails ? "Hide Details" : "Show Details"}</button>
          </div>
        }
        {!values.name && <h2>No card added yet.</h2>}
      </div>

      <button onClick={(addCard)}>Add new card</button>

    </div>

  );
  function addCard() {
    navigate("/addCard");
  }
  function makePayment() {
    navigate("/makePayment");
  }
  function showCardDetails() {
    setShowAllDetails(!showAllDetails);

  }
}

export default Home;