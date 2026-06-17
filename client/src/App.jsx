import { NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import PresupuestoEditor from "./pages/PresupuestoEditor.jsx";
import Plantillas from "./pages/Plantillas.jsx";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>Presupuestos</h1>
        <nav>
          <NavLink to="/" end>
            Histórico
          </NavLink>
          <NavLink to="/plantillas">Catálogo</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/presupuestos/:id" element={<PresupuestoEditor />} />
          <Route path="/plantillas" element={<Plantillas />} />
        </Routes>
      </main>
    </div>
  );
}
