import { useEffect, useRef } from 'react';

export const useEqualCardHeights = (dependency?: any) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const equalizeHeights = () => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const cards = container.querySelectorAll('[data-card]') as NodeListOf<HTMLElement>;
    
    if (cards.length === 0) return;

    const heights: number[] = [];
    cards.forEach((card) => {
      card.style.height = 'auto';
      heights.push(card.offsetHeight);
    });

    const maxHeight = Math.max(...heights);
    if (maxHeight > 0) {
      cards.forEach((card) => {
        card.style.height = `${maxHeight}px`;
      });
    }
  };

  useEffect(() => {
    equalizeHeights();

    const handleResize = () => {
      equalizeHeights();
    };

    window.addEventListener('resize', handleResize);

    const container = containerRef.current;
    if (container) {
      const images = container.querySelectorAll('img');
      const imageLoadPromises = Array.from(images).map((img) => {
        if (img.complete) return Promise.resolve();
        return new Promise((resolve) => {
          img.onload = resolve;
          img.onerror = resolve;
        });
      });

      Promise.all(imageLoadPromises).then(() => {
        setTimeout(equalizeHeights, 100);
      });
    }

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [dependency]);

  return containerRef;
};

