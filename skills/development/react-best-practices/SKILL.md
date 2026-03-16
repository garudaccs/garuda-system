# React Best Practices

## Metadata
- **ID:** react-best-practices
- **Version:** 1.0.0
- **Source:** vercel-labs/agent-skills
- **Agents:** arjun, michael, priya
- **Tags:** react, nextjs, performance, frontend

## Purpose
Guidelines for writing performant, maintainable React and Next.js code.

## Key Principles

### 1. Component Structure
```jsx
// Prefer functional components with hooks
const MyComponent = ({ data }) => {
  const [state, setState] = useState(initialState);

  useEffect(() => {
    // Side effects here
  }, [dependencies]);

  return <div>{/* JSX */}</div>;
};
```

### 2. Performance Optimization
- Use `React.memo()` for expensive components
- Implement `useMemo()` for computed values
- Use `useCallback()` for event handlers passed as props
- Lazy load components with `React.lazy()` and `Suspense`

### 3. Next.js Specific
- Use App Router (app/) over Pages Router (pages/)
- Implement Server Components by default
- Use `'use client'` directive only when needed
- Optimize images with `next/image`
- Use `next/link` for navigation

### 4. State Management
- Local state: `useState`
- Complex state: `useReducer`
- Global state: Context API or Zustand
- Server state: React Query / SWR

### 5. Code Organization
```
/components
  /ui          # Reusable UI components
  /features    # Feature-specific components
  /layouts     # Layout components
/hooks         # Custom hooks
/lib           # Utility functions
/types         # TypeScript types
```

## Checklist Before Commit
- [ ] No console.log in production code
- [ ] PropTypes or TypeScript types defined
- [ ] Accessibility attributes (aria-*)
- [ ] Responsive design implemented
- [ ] Error boundaries for critical sections
