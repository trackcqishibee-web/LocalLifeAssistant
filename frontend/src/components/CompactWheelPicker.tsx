import { useRef, useEffect, useState } from 'react';

interface CompactWheelPickerProps {
  items: string[];
  selectedIndex: number;
  onChange: (index: number) => void;
  label: string;
}

export function CompactWheelPicker({ items, selectedIndex, onChange, label }: CompactWheelPickerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const itemWidth = 100;

  useEffect(() => {
    if (scrollRef.current) {
      const offset = selectedIndex * itemWidth;
      scrollRef.current.scrollLeft = offset;
    }
  }, [selectedIndex]);

  const handleScroll = () => {
    if (!scrollRef.current || isDragging) return;
    
    const scrollLeft = scrollRef.current.scrollLeft;
    const scrollWidth = scrollRef.current.scrollWidth;
    const containerWidth = scrollRef.current.offsetWidth;
    const maxScroll = scrollWidth - containerWidth;
    
    // Calculate the index based on scroll position
    let index = Math.round(scrollLeft / itemWidth);
    
    // Clamp index to valid range
    index = Math.max(0, Math.min(index, items.length - 1));
    
    // If we're near the end, ensure we can select the last item
    if (scrollLeft >= maxScroll - 10) {
      index = items.length - 1;
    }
    
    if (index !== selectedIndex && index >= 0 && index < items.length) {
      onChange(index);
    }
  };

  const handleScrollEnd = () => {
    setIsDragging(false);
    if (!scrollRef.current) return;
    
    const scrollLeft = scrollRef.current.scrollLeft;
    const scrollWidth = scrollRef.current.scrollWidth;
    const containerWidth = scrollRef.current.offsetWidth;
    const maxScroll = scrollWidth - containerWidth;
    
    // Calculate the index based on scroll position
    let index = Math.round(scrollLeft / itemWidth);
    
    // Clamp index to valid range
    index = Math.max(0, Math.min(index, items.length - 1));
    
    // For the last item, ensure we can scroll to it
    if (index === items.length - 1 && scrollLeft < maxScroll - 5) {
      // If we're near the end but not quite there, snap to the last item
      const targetScroll = (items.length - 1) * itemWidth;
      scrollRef.current.scrollTo({
        left: targetScroll,
        behavior: 'smooth'
      });
      if (index !== selectedIndex) {
        onChange(index);
      }
      return;
    }
    
    const targetScroll = index * itemWidth;
    
    scrollRef.current.scrollTo({
      left: targetScroll,
      behavior: 'smooth'
    });
    
    if (index !== selectedIndex && index >= 0 && index < items.length) {
      onChange(index);
    }
  };

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;

    let scrollTimeout: NodeJS.Timeout;
    
    const onScroll = () => {
      setIsDragging(true);
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(handleScrollEnd, 150);
      handleScroll();
    };

    element.addEventListener('scroll', onScroll);
    
    return () => {
      element.removeEventListener('scroll', onScroll);
      clearTimeout(scrollTimeout);
    };
  }, [selectedIndex, items.length]);

  return (
    <div className="flex flex-col items-center flex-1">
      <p className="text-[10px] mb-1.5" style={{ color: '#5E574E' }}>{label}</p>
      <div className="relative w-full h-[50px]">
        <div 
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/80 backdrop-blur-sm border-2 rounded-lg pointer-events-none z-0"
          style={{ 
            width: `${itemWidth}px`,
            height: '44px',
            borderColor: 'rgba(118, 193, 178, 0.8)'
          }}
        />
        
        <div 
          className="absolute top-0 bottom-0 left-0 w-12 pointer-events-none z-20"
          style={{
            background: 'linear-gradient(to right, #FCFBF9 0%, transparent 100%)'
          }}
        />
        
        <div 
          className="absolute top-0 bottom-0 right-0 w-12 pointer-events-none z-20"
          style={{
            background: 'linear-gradient(to left, #FCFBF9 0%, transparent 100%)'
          }}
        />
        
        <div
          ref={scrollRef}
          className="overflow-x-scroll overflow-y-hidden scrollbar-hide h-full"
          style={{
            scrollSnapType: 'x mandatory',
            WebkitOverflowScrolling: 'touch'
          }}
        >
          <div className="flex items-center h-full">
            <div style={{ width: `calc(50% - ${itemWidth / 2}px)`, flexShrink: 0 }} />
            
            {items.map((item, index) => {
              const distance = Math.abs(index - selectedIndex);
              const opacity = Math.max(0.3, 1 - distance * 0.35);
              const scale = Math.max(0.75, 1 - distance * 0.15);
              const isSelected = index === selectedIndex;
              
              return (
                <div
                  key={index}
                  className="flex items-center justify-center transition-all duration-200 relative z-10"
                  style={{
                    width: `${itemWidth}px`,
                    height: '50px',
                    flexShrink: 0,
                    scrollSnapAlign: 'center',
                    opacity,
                    transform: `scale(${scale})`,
                  }}
                  onClick={() => {
                    if (scrollRef.current) {
                      const targetScroll = index * itemWidth;
                      scrollRef.current.scrollTo({
                        left: targetScroll,
                        behavior: 'smooth'
                      });
                      // Update after scroll animation
                      setTimeout(() => {
                        onChange(index);
                      }, 100);
                    } else {
                      onChange(index);
                    }
                  }}
                >
                  <span 
                    className="whitespace-nowrap px-2 text-center"
                    style={{
                      color: isSelected ? '#221A13' : '#5E574E',
                      fontFamily: isSelected ? 'Aladin, cursive' : 'inherit',
                      fontSize: isSelected ? '15px' : '12px',
                      fontWeight: isSelected ? '500' : '400'
                    }}
                  >
                    {item}
                  </span>
                </div>
              );
            })}
            
            <div style={{ width: `calc(50% - ${itemWidth / 2}px)`, flexShrink: 0 }} />
          </div>
        </div>
      </div>
    </div>
  );
}

