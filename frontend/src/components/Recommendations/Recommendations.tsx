import axios from "axios";
import React, { use, useEffect, useState } from "react";
import { set, useForm } from "react-hook-form";
import "./Recommendations.css";
import { useNavigate } from "react-router-dom";

function Recommendations() {
    const categoryImageMap = {
        "Music Stores - Musical Instruments": "MusicStores.jpg",
        "Digital Goods - Games": "DigitalGoodsGames.jpg",
        "Sporting Goods Stores": "SportingGoods.jpg",
        "Furniture, Home Furnishings, and Equipment Stores": "FurnitureHome.jpg",
        "Amusement Parks, Carnivals, Circuses": "AmusementParks.jpg",
        "Digital Goods - Media, Books, Apps": "DigitalGoodsMedia.jpg",
        "Airlines": "Airlines.jpg",
        "Book Stores": "BookStores.jpg",
        "Cosmetic Stores": "CosmeticStores.jpg",
        "Eating Places and Restaurants": "EatingPlaces.jpg",
        "Discount Stores": "DiscountStores.jpg",
        "Fast Food Restaurants": "FastFood.jpg",
        "Miscellaneous Home Furnishing Stores": "MiscellaneousHome.jpg",
        "Motion Picture Theaters": "MotionPicture.jpg",
        "Precious Stones and Metals": "PreciousStones.jpg",
        "Shoe Stores": "ShoeStores.jpg",
        "Taxicabs and Limousines": "TaxicabsandLimousines.jpg"
    };
    const recommendationsUrl = "http://localhost:8000/recommendations";

    const [recommendations, setRecommendations] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchRecommendations = async () => {
            try {
                const token = localStorage.getItem("token");

                const response = await axios.get(recommendationsUrl, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });

                setRecommendations(response.data.categories || response.data);
                //setRecommendations(["Alimente", "Transport", "Divertisment", "Sănătate", "Educație"]);
                setIsLoading(false);
            } catch (err) {
                console.error("Eroare la preluarea recomandărilor:", err);
                setError("Nu am putut încărca recomandările.");
                setIsLoading(false);
            }
        };

        fetchRecommendations();
    }, []);

    return (
        <>
            <h2>Top Recommendations</h2>
            <div className="recommendations-container">
                {isLoading && <p>Se calculează recomandările...</p>}

                {error && <p className="error-message">{error}</p>}

                {!isLoading && !error && recommendations.length === 0 && (
                    <p>Momentan nu avem recomandări noi pentru tine.</p>
                )}

                {!isLoading && !error && recommendations.length > 0 && (
                    <ul className="recommendations-list">
                        {recommendations.map((category, index) => {

                            const fileName = categoryImageMap[category] || "default.png";
                            return (
                                <li key={index} className="recommendation-card">
                                    <img
                                        src={`/categoryPhotos/${fileName}`}
                                        alt={category}
                                        className="category-image"
                                    />
                                    <h3>{category}</h3>
                                </li>
                            );
                        })}
                    </ul>

                )}
            </div>
            <button className="back-button" onClick={() => window.history.back()}>Back</button>

        </>
    );
}


export default Recommendations;
