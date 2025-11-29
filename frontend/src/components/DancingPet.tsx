import React from 'react';

interface DancingPetProps {
  type?: 'dog' | 'cat';
  size?: number;
  className?: string;
  gifSrc?: string;
}

const DancingPet: React.FC<DancingPetProps> = ({ type = 'dog', size = 48, className = '', gifSrc }) => {
  const petColor = '#76C1B2'; // Brand color to match existing icons
  
  if (gifSrc) {
    return (
      <div 
        className={`dancing-pet-container ${className}`}
        style={{
          width: size,
          height: size,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <img
          src={gifSrc}
          alt="Dancing pet animation"
          style={{
            width: size,
            height: size,
            objectFit: 'contain',
            filter: 'drop-shadow(0 2px 4px rgba(118, 193, 178, 0.3))',
          }}
        />
      </div>
    );
  }
  
  return (
    <div 
      className={`dancing-pet-container ${className}`}
      style={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className="dancing-pet"
        style={{
          animation: 'dance 1.5s ease-in-out infinite',
        }}
      >
        {type === 'dog' ? (
          // Dancing Dog
          <g>
            {/* Body */}
            <ellipse
              cx="50"
              cy="60"
              rx="25"
              ry="20"
              fill={petColor}
              style={{
                animation: 'bounce 1.5s ease-in-out infinite',
                transformOrigin: '50% 60%',
              }}
            />
            {/* Head */}
            <circle
              cx="50"
              cy="35"
              r="18"
              fill={petColor}
              style={{
                animation: 'wiggle 1.5s ease-in-out infinite',
                transformOrigin: '50% 35%',
              }}
            />
            {/* Ears */}
            <ellipse
              cx="40"
              cy="25"
              rx="6"
              ry="10"
              fill={petColor}
              style={{
                animation: 'earWiggle 1.5s ease-in-out infinite',
                transformOrigin: '40% 25%',
              }}
            />
            <ellipse
              cx="60"
              cy="25"
              rx="6"
              ry="10"
              fill={petColor}
              style={{
                animation: 'earWiggle 1.5s ease-in-out infinite 0.2s',
                transformOrigin: '60% 25%',
              }}
            />
            {/* Eyes */}
            <circle cx="45" cy="32" r="3" fill="white" />
            <circle cx="55" cy="32" r="3" fill="white" />
            {/* Nose */}
            <ellipse cx="50" cy="38" rx="2" ry="1.5" fill="white" />
            {/* Tail */}
            <path
              d="M 25 60 Q 15 50, 10 45 Q 5 40, 8 35"
              stroke={petColor}
              strokeWidth="4"
              fill="none"
              strokeLinecap="round"
              style={{
                animation: 'tailWag 1.5s ease-in-out infinite',
                transformOrigin: '25% 60%',
              }}
            />
            {/* Legs */}
            <rect
              x="35"
              y="75"
              width="5"
              height="12"
              rx="2"
              fill={petColor}
              style={{
                animation: 'legBounce 1.5s ease-in-out infinite',
                transformOrigin: '35% 75%',
              }}
            />
            <rect
              x="60"
              y="75"
              width="5"
              height="12"
              rx="2"
              fill={petColor}
              style={{
                animation: 'legBounce 1.5s ease-in-out infinite 0.3s',
                transformOrigin: '60% 75%',
              }}
            />
          </g>
        ) : (
          // Dancing Cat
          <g>
            {/* Body */}
            <ellipse
              cx="50"
              cy="60"
              rx="22"
              ry="18"
              fill={petColor}
              style={{
                animation: 'bounce 1.5s ease-in-out infinite',
                transformOrigin: '50% 60%',
              }}
            />
            {/* Head */}
            <circle
              cx="50"
              cy="35"
              r="16"
              fill={petColor}
              style={{
                animation: 'wiggle 1.5s ease-in-out infinite',
                transformOrigin: '50% 35%',
              }}
            />
            {/* Ears (pointed) */}
            <path
              d="M 42 20 L 38 30 L 46 30 Z"
              fill={petColor}
              style={{
                animation: 'earWiggle 1.5s ease-in-out infinite',
                transformOrigin: '42% 25%',
              }}
            />
            <path
              d="M 58 20 L 62 30 L 54 30 Z"
              fill={petColor}
              style={{
                animation: 'earWiggle 1.5s ease-in-out infinite 0.2s',
                transformOrigin: '58% 25%',
              }}
            />
            {/* Eyes */}
            <ellipse cx="45" cy="32" rx="3" ry="4" fill="white" />
            <ellipse cx="55" cy="32" rx="3" ry="4" fill="white" />
            {/* Nose */}
            <path
              d="M 50 38 L 48 42 L 52 42 Z"
              fill="white"
            />
            {/* Tail (curved) */}
            <path
              d="M 28 60 Q 18 50, 12 40 Q 6 30, 10 25"
              stroke={petColor}
              strokeWidth="4"
              fill="none"
              strokeLinecap="round"
              style={{
                animation: 'tailWag 1.5s ease-in-out infinite',
                transformOrigin: '28% 60%',
              }}
            />
            {/* Legs */}
            <rect
              x="36"
              y="75"
              width="4"
              height="10"
              rx="2"
              fill={petColor}
              style={{
                animation: 'legBounce 1.5s ease-in-out infinite',
                transformOrigin: '36% 75%',
              }}
            />
            <rect
              x="60"
              y="75"
              width="4"
              height="10"
              rx="2"
              fill={petColor}
              style={{
                animation: 'legBounce 1.5s ease-in-out infinite 0.3s',
                transformOrigin: '60% 75%',
              }}
            />
          </g>
        )}
      </svg>
      
      <style>{`
        @keyframes dance {
          0%, 100% {
            transform: translateY(0) rotate(0deg);
          }
          25% {
            transform: translateY(-8px) rotate(-5deg);
          }
          50% {
            transform: translateY(-12px) rotate(0deg);
          }
          75% {
            transform: translateY(-8px) rotate(5deg);
          }
        }
        
        @keyframes bounce {
          0%, 100% {
            transform: scaleY(1);
          }
          50% {
            transform: scaleY(0.95);
          }
        }
        
        @keyframes wiggle {
          0%, 100% {
            transform: rotate(0deg);
          }
          25% {
            transform: rotate(-8deg);
          }
          75% {
            transform: rotate(8deg);
          }
        }
        
        @keyframes earWiggle {
          0%, 100% {
            transform: rotate(0deg);
          }
          50% {
            transform: rotate(15deg);
          }
        }
        
        @keyframes tailWag {
          0%, 100% {
            transform: rotate(0deg);
          }
          25% {
            transform: rotate(-20deg);
          }
          75% {
            transform: rotate(20deg);
          }
        }
        
        @keyframes legBounce {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-4px);
          }
        }
        
        .dancing-pet {
          filter: drop-shadow(0 2px 4px rgba(118, 193, 178, 0.3));
        }
      `}</style>
    </div>
  );
};

export default DancingPet;

