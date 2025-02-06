import { Loader } from 'lucide-react';
import React from 'react';

const Loading = ({ message }) => {
    return (
        <div className="flex flex-col items-center justify-center p-4 animate-pulse">
            <Loader />
            <p className="text-gray-800">{message}</p>
        </div>
    );
};


export default Loading;