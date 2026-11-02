# React

- Give list items a stable key from the data, never the array index.
- Don't look up DOM elements directly (`document.getElementById`, `querySelector`); use refs.
- List every value a hook uses in its dependency array (`useEffect`, `useMemo`, `useCallback`).
- One component per file, and keep components small. Move logic that isn't about display into hooks or plain functions.
