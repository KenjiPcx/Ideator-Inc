import Image from "next/image";

interface HeaderProps {
  setUserEmail: (email: string) => void;
}

export default function Header({ setUserEmail }: HeaderProps) {
  return (
    <div className="flex justify-between items-center">
      <h1 className="text-4xl font-bold text-white">
        Ideator Inc
        <span className="text-blue-400 ml-2 text-lg font-normal">
          AI-Powered Startup Research Lab
        </span>
      </h1>
      
      <div className="relative group">
        <input
          type="email"
          placeholder="Enter your email"
          className="px-4 py-2 rounded bg-gray-700 text-white w-64"
          onChange={(e) => setUserEmail(e.target.value)}
        />
        <div className="absolute hidden group-hover:block right-0 top-full mt-2 p-2 bg-gray-800 text-white text-sm rounded-lg w-64">
          Leave your email and you will be sent the artifacts when done
        </div>
      </div>
    </div>
  );
}
