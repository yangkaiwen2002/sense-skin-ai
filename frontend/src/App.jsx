import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import ItemDetail from './pages/ItemDetail'
import Compare from './pages/Compare'
import RentVsBuy from './pages/RentVsBuy'
import Watchlist from './pages/Watchlist'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/item/:itemId" element={<ItemDetail />} />
          <Route path="/compare/:itemId" element={<Compare />} />
          <Route path="/rent-vs-buy" element={<RentVsBuy />} />
          <Route path="/watchlist" element={<Watchlist />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
