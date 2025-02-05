import { useState, useLayoutEffect, useRef } from "react";
import { Document, Page } from "react-pdf";
import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import useResizeObserver from '@react-hook/resize-observer';

const useDimensions = (target) => {
    const [width, setWidth] = useState(null);
    const [height, setHeight] = useState(null);

    useLayoutEffect(() => {
        setWidth(target.current.getBoundingClientRect().width)
        setHeight(target.current.getBoundingClientRect().height)
    }, [target]);

    useResizeObserver(target, (entry) => {
        setWidth(entry.contentRect.width);
        setHeight(entry.contentRect.height);
    });
    return { width, height };
};

export default function PdfViewer({ memoizedPdfPointer }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [numPages, setNumPages] = useState<number | null>(null);
    const [pageNumber, setPageNumber] = useState(1);
    const {width, height} = useDimensions(containerRef);

    const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
        setPageNumber(1);
    };

    return (
        <div className="h-full flex flex-col items-center">
            {/* Container to ensure the page is centered and contained */}
            <div ref={containerRef} className="h-full max-h-[85vh] flex justify-center items-center overflow-hidden">
                <Document file={memoizedPdfPointer} onLoadSuccess={onDocumentLoadSuccess}>
                    <Page
                        pageNumber={pageNumber}
                        className="max-w-full max-h-full"
                        height={height}
                    />
                </Document>
            </div>

            {/* Navigation Buttons */}
            <div className="flex mt-4 justify-center">
                <button
                    onClick={() => setPageNumber(prev => Math.max(prev - 1, 1))}
                    disabled={pageNumber <= 1}
                    className="p-2 mx-2 bg-gray-300 rounded disabled:opacity-50"
                >
                    <ChevronLeft />
                </button>
                <button
                    onClick={() => setPageNumber(prev => Math.min(prev + 1, numPages ?? 1))}
                    disabled={pageNumber >= (numPages ?? 1)}
                    className="p-2 mx-2 bg-gray-300 rounded disabled:opacity-50"
                >
                    <ChevronRight />
                </button>
            </div>
        </div>
    );
}
