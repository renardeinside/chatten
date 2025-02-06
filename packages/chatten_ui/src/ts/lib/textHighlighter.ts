import Fuse from "fuse.js";
import { useMemo } from "react";

const stopWords = new Set(["on", "in", "a", "an", "the", "is", "at", "it", "of", "to", "and", "we"]);

const useTextHighlighter = (textToHighlight: string) => {
    const fuse = useMemo(() => {
        return new Fuse(textToHighlight.split("\n"), { includeMatches: true, threshold: 0.4});
    }, [textToHighlight]);

    const textHighlighter = (textChunk: string) => {
        const cleanedChunk = textChunk.trim();

        if (cleanedChunk.length <= 1 || stopWords.has(cleanedChunk.toLowerCase())) {
            return textChunk; // Ignore spaces and common stop words
        }

        const result = fuse.search(cleanedChunk);
        if (result.length > 0) {
            return `<mark>${textChunk}</mark>`;
        }
        return textChunk;
    };

    return textHighlighter;
};

export default useTextHighlighter;
