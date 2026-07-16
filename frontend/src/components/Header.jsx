import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <nav className="container mx-auto flex items-center gap-6">
        <Link to="/" className="text-xl font-bold text-red-500">F1 Telemetry</Link>
        <Link to="/" className="text-gray-300 hover:text-white">Home</Link>
      </nav>
    </header>
  )
}
