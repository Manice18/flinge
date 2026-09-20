import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App.jsx";
import HeartbreakPage from "./pages/HeartbreakPage.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/heartbreak" element={<HeartbreakPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
