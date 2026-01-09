import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import AddCard from "./components/AddCard/AddCard";
import Home from "./components/Home/Home";
import Login from "./components/Login/Login";
import ProtectedRoute from "./ProtectedRouter";
import Register from "./components/Register/Register";
import MakePayment from "./components/MakePayment/MakePayment";
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/makePayment" 
          element={
            <ProtectedRoute>
              <MakePayment />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/addCard" 
          element={
            <ProtectedRoute>
              <AddCard />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}
export default App;