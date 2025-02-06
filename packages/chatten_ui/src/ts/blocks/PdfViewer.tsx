import { useState, useLayoutEffect, useRef } from "react";
import { Document, Page } from "react-pdf";
import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import useResizeObserver from '@react-hook/resize-observer';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

import { pdfjs } from 'react-pdf';
import useTextHighlighter from "../lib/textHighlighter";
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;


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

export default function PdfViewer({ memoizedPdfPointer, initialPageNumber, textToHighlight }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [numPages, setNumPages] = useState<number | null>(null);
    const [pageNumber, setPageNumber] = useState(initialPageNumber);
    const { height } = useDimensions(containerRef);
    const textHighlighter = useTextHighlighter(textToHighlight);

    const onDocumentLoadSuccess = async ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
    };
    return (
        <div >
            {/* Container to ensure the page is centered and contained */}
            <div ref={containerRef} className="overflow-hidden w-full flex justify-center items-center h-[85vh]">
                <Document file={memoizedPdfPointer} onLoadSuccess={onDocumentLoadSuccess} onItemClick={({ pageNumber }) => {
                    // set the page number to the clicked page
                    setPageNumber(pageNumber);
                }}>
                    <Page
                        pageNumber={pageNumber}
                        height={height}
                        customTextRenderer={({ str }) => textHighlighter(str)}
                    />
                </Document>
            </div>

            {/* Navigation Buttons */}
            <div className="flex mt-4 justify-center w-full">
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
