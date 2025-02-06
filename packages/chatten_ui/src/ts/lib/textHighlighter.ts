import Fuse from "fuse.js";
import { useMemo } from "react";

const stopWords = new Set(["on", "in", "a", "an", "the", "is", "at", "it", "of", "to", "and", "we"]);

const useTextHighlighter = (textToHighlight: string) => {
    // this is a really complex magic but I'll try to explain it
    // react-pdf throws text chunks (usually the lines of the pdf) to the customTextRenderer
    // this function is called for every chunk of text in the pdf
    // the chunk is then cleaned and checked against the fuse search
    // if it matches, it's highlighted by adding a <mark> tag around it
    // Notably, the threshold is set to 0.4, which means that the match has to be at least 40% similar to the search
    // So some words might be highlighted outside of the main query but it's not a big deal
    // Consider it "contextual" highlighting
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
