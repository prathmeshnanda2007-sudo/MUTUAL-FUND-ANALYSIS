import React, { useState, useEffect } from 'react';
import { ArrowRight, Clock, Menu, X } from 'lucide-react';
import { Shader, Swirl, ChromaFlow, FlutedGlass, FilmGrain } from 'shaders/react';

function App() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [time, setTime] = useState('');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [platformStats, setPlatformStats] = useState({ fundsTracked: 0, avgReturns: 0.0, activeUsers: 0 });

  // Update London time
  useEffect(() => {
    const updateClock = () => {
      const formatter = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Europe/London',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
      setTime(formatter.format(new Date()));
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  // Check performance preference and fetch data
  useEffect(() => {
    // High/Low FPS toggle based on user OS preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handleChange = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    // Fetch live API data from backend
    fetch('http://localhost:8000/api/platform-stats')
      .then(res => res.json())
      .then(data => setPlatformStats(data))
      .catch(err => console.error("API error:", err));

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <div className="w-full min-h-screen bg-[#EFEFEF]">
      
      {/* =========================================================================
          SECTION 1: HERO
          ========================================================================= */}
      <section className="relative w-full h-[100svh] flex flex-col">
        
        {/* Animated Shader Background (or CSS Fallback for low FPS) */}
        <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
          {!prefersReducedMotion ? (
            <Shader>
              <Swirl colorA="#ffffff" colorB="#f0f0f0" detail={1.7} />
              <ChromaFlow 
                baseColor="#ffffff" 
                downColor="#ff5f03" 
                leftColor="#ff5f03" 
                rightColor="#ff5f03" 
                upColor="#ff5f03" 
                momentum={13} 
                radius={3.5} 
              />
              <FlutedGlass 
                aberration={0.61} 
                angle={31} 
                frequency={8} 
                highlight={0.12} 
                highlightSoftness={0} 
                lightAngle={-90} 
                refraction={4} 
                shape="rounded" 
                softness={1} 
                speed={0.15} 
              />
              <FilmGrain strength={0.05} />
            </Shader>
          ) : (
            <div className="w-full h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-orange-100 via-white to-gray-100 opacity-60"></div>
          )}
        </div>

        {/* Navigation */}
        <nav className="relative z-20 mx-auto w-full max-w-[1440px] p-2 sm:p-3">
          <div className="flex items-center justify-between bg-white rounded-full p-[5px]">
            {/* LEFT */}
            <div className="flex items-center gap-6">
              <div className="flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 bg-gray-900 rounded-full text-white text-[10px] sm:text-[11px] font-bold tracking-tight">AX</div>
              <div className="hidden md:flex items-center gap-6 text-[14px] text-gray-900">
                <a href="#" className="hover:text-gray-500 transition-colors duration-300">Live NAV</a>
                <a href="#" className="hover:text-gray-500 transition-colors duration-300">Analytics</a>
                <a href="#" className="hover:text-gray-500 transition-colors duration-300">Performance</a>
                <a href="#" className="hover:text-gray-500 transition-colors duration-300">Reports</a>
              </div>
            </div>
            {/* RIGHT */}
            <div className="hidden md:flex items-center gap-6">
              <span className="hidden lg:block text-[13px] text-gray-600">Tracking {platformStats.fundsTracked || 'live'} mutual funds with {platformStats.avgReturns}% avg returns</span>
              <div className="flex items-center gap-1.5 text-[13px] text-gray-600">
                <Clock size={14} />
                <span>{time} in London</span>
              </div>
              <a href="http://localhost:8000/login" className="group flex items-center bg-gray-900 text-white text-[13px] font-medium rounded-full pl-5 pr-2 py-2 gap-3 cursor-pointer hover:bg-gray-800 transition-colors">
                <div className="overflow-hidden h-[20px] relative w-auto min-w-[115px] flex items-center">
                   <div className="flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                     <span className="h-[20px] flex items-center">Dashboard Login</span>
                     <span className="h-[20px] flex items-center">Dashboard Login</span>
                   </div>
                </div>
                <div className="flex items-center justify-center w-6 h-6 bg-white rounded-full transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-rotate-45">
                  <ArrowRight size={12} className="text-gray-900" />
                </div>
              </a>
            </div>
            {/* MOBILE TOGGLE */}
            <button className="md:hidden flex items-center justify-center w-9 h-9 bg-gray-900 rounded-full text-white" onClick={() => setIsMobileMenuOpen(true)}>
              <Menu size={16} />
            </button>
          </div>
        </nav>

        {/* Mobile Menu Overlay */}
        <div className={`fixed inset-0 z-50 flex flex-col justify-end transition-opacity duration-500 md:hidden ${isMobileMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
          <div className="absolute inset-0 bg-black/60" onClick={() => setIsMobileMenuOpen(false)} />
          <div className={`relative bg-white rounded-2xl mx-3 mb-3 p-6 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${isMobileMenuOpen ? 'translate-y-0' : 'translate-y-[120%]'}`}>
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-1.5 text-[13px] text-gray-600">
                <Clock size={14} />
                <span>{time} in London</span>
              </div>
              <button onClick={() => setIsMobileMenuOpen(false)} className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 transition-colors rounded-full">
                <X size={16} />
              </button>
            </div>
            <div className="flex flex-col gap-4 text-[28px] sm:text-[32px] font-medium text-gray-900 mb-8">
                <a href="#">Live NAV</a>
                <a href="#">Analytics</a>
                <a href="#">Performance</a>
                <a href="#">Reports</a>
            </div>
            <a href="http://localhost:8000/login" className="flex items-center justify-between w-full bg-gray-900 text-white rounded-full pl-6 pr-2 py-2">
              <span className="text-[15px] font-medium">Dashboard Login</span>
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                <ArrowRight size={16} className="text-gray-900" />
              </div>
            </a>
          </div>
        </div>

        {/* Hero Content */}
        <div className="relative z-20 flex-1 flex flex-col justify-end mx-auto w-full max-w-[1440px] px-5 sm:px-8 lg:px-12 pb-14 sm:pb-16 lg:pb-20">
          <div className="text-[13px] sm:text-[14px] text-gray-900 tracking-wide mb-5 sm:mb-8">Mainframe Analytics</div>
          <h1 className="font-medium leading-[1.08] tracking-[-0.03em] text-gray-900 text-[clamp(1.75rem,7vw,4.2rem)] sm:text-[clamp(2.5rem,5vw,4.2rem)]">
            We craft data-driven insights <br className="hidden sm:block" /><span className="sm:hidden"> </span>
            for investors ready to dominate <br className="hidden sm:block" /><span className="sm:hidden"> </span>
            their portfolios online.
          </h1>
          <div className="mt-8 sm:mt-12 flex flex-col sm:flex-row gap-4 sm:gap-5 items-start sm:items-center">
            <a href="http://localhost:8000/login" className="group flex items-center bg-[#F26522] hover:bg-[#e05a1a] text-white text-[13px] sm:text-[14px] rounded-full pl-5 sm:pl-6 pr-2 py-2 gap-3 transition-colors duration-300">
              <div className="overflow-hidden h-[20px] relative w-auto min-w-[130px] flex items-center">
                 <div className="flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                   <span className="h-[20px] flex items-center">Dashboard Login</span>
                   <span className="h-[20px] flex items-center">Dashboard Login</span>
                 </div>
              </div>
              <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 bg-white rounded-full transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-rotate-45">
                <ArrowRight size={14} className="text-[#F26522]" />
              </div>
            </a>
            
            <div className="flex items-center gap-2 bg-white rounded-[4px] px-3 py-1.5 shadow-[0_2px_8px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow duration-300">
              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-[#E8704E] fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="m19.6 66.5 19.7-11 .3-1-.3-.5h-1l-3.3-.2-11.2-.3L14 53l-9.5-.5-2.4-.5L0 49l.2-1.5 2-1.3 2.9.2 6.3.5 9.5.6 6.9.4L38 49.1h1.6l.2-.7-.5-.4-.4-.4L29 41l-10.6-7-5.6-4.1-3-2-1.5-2-.6-4.2 2.7-3 3.7.3.9.2 3.7 2.9 8 6.1L37 36l1.5 1.2.6-.4.1-.3-.7-1.1L33 25l-6-10.4-2.7-4.3-.7-2.6c-.3-1-.4-2-.4-3l3-4.2L28 0l4.2.6L33.8 2l2.6 6 4.1 9.3L47 29.9l2 3.8 1 3.4.3 1h.7v-.5l.5-7.2 1-8.7 1-11.2.3-3.2 1.6-3.8 3-2L61 2.6l2 2.9-.3 1.8-1.1 7.7L59 27.1l-1.5 8.2h.9l1-1.1 4.1-5.4 6.9-8.6 3-3.5L77 13l2.3-1.8h4.3l3.1 4.7-1.4 4.9-4.4 5.6-3.7 4.7-5.3 7.1-3.2 5.7.3.4h.7l12-2.6 6.4-1.1 7.6-1.3 3.5 1.6.4 1.6-1.4 3.4-8.2 2-9.6 2-14.3 3.3-.2.1.2.3 6.4.6 2.8.2h6.8l12.6 1 3.3 2 1.9 2.7-.3 2-5.1 2.6-6.8-1.6-16-3.8-5.4-1.3h-.8v.4l4.6 4.5 8.3 7.5L89 80.1l.5 2.4-1.3 2-1.4-.2-9.2-7-3.6-3-8-6.8h-.5v.7l1.8 2.7 9.8 14.7.5 4.5-.7 1.4-2.6 1-2.7-.6-5.8-8-6-9-4.7-8.2-.5.4-2.9 30.2-1.3 1.5-3 1.2-2.5-2-1.4-3 1.4-6.2 1.6-8 1.3-6.4 1.2-7.9.7-2.6v-.2H49L43 72l-9 12.3-7.2 7.6-1.7.7-3-1.5.3-2.8L24 86l10-12.8 6-7.9 4-4.6-.1-.5h-.3L17.2 77.4l-4.7.6-2-2 .2-3 1-1 8-5.5Z"/>
              </svg>
              <span className="text-[13px] sm:text-[14px] font-medium text-gray-900">Certified Partner</span>
              <span className="text-[10px] sm:text-[11px] bg-gray-900 text-white px-1.5 sm:px-2 py-0.5 rounded ml-1">Featured</span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 2: ABOUT
          ========================================================================= */}
      <section className="bg-white pt-16 sm:pt-20 lg:pt-32 pb-12 sm:pb-16 lg:pb-24 overflow-hidden relative z-20">
        <div className="mx-auto max-w-[1440px]">
          {/* Badge row */}
          <div className="px-5 sm:px-8 lg:px-12 flex items-center gap-3 mb-6 sm:mb-8">
            <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-gray-900 text-white text-[11px] sm:text-[12px] font-semibold flex items-center justify-center">1</div>
            <div className="text-[12px] sm:text-[13px] font-medium border border-gray-200 rounded-full px-3 sm:px-4 py-1 sm:py-1.5">Introducing Platform</div>
          </div>
          
          <div className="px-5 sm:px-8 lg:px-12">
            <h2 className="text-[clamp(1.5rem,4vw,3.2rem)] font-medium leading-[1.12] tracking-[-0.02em] text-gray-900 mb-12 sm:mb-16 lg:mb-28">
              Strategy-led creatives, delivering <br /> results in digital and beyond.
            </h2>
          </div>

          {/* Content Area */}
          <div className="px-5 sm:px-8 lg:px-12">
            {/* Mobile/Tablet Stacked */}
            <div className="lg:hidden flex flex-col gap-6">
              <p className="text-[15px] sm:text-[17px] leading-[1.6] font-medium text-gray-900">
                Through research, creative thinking and iteration we help growing brands realize their digital full potential.
              </p>
              <a href="http://localhost:8000/login" className="group self-start flex items-center bg-[#F26522] hover:bg-[#e05a1a] text-white text-[13px] rounded-full pl-5 pr-2 py-2 gap-3 transition-colors duration-300">
                <div className="overflow-hidden h-[20px] relative w-auto min-w-[120px] flex items-center">
                   <div className="flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                     <span className="h-[20px] flex items-center">Explore Dashboard</span>
                     <span className="h-[20px] flex items-center">Explore Dashboard</span>
                   </div>
                </div>
                <div className="flex items-center justify-center w-6 h-6 bg-white rounded-full transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-rotate-45">
                  <ArrowRight size={12} className="text-[#F26522]" />
                </div>
              </a>
              <div className="flex flex-col sm:flex-row gap-4 sm:gap-5 mt-4">
                <img src="https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260516_090123_74be96d4-9c1b-40cf-932a-96f4f4babed3.png&w=1280&q=85" alt="Analytics 1" className="sm:w-[45%] aspect-[438/346] rounded-xl sm:rounded-2xl object-cover" />
                <img src="https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260516_090133_c157d30b-a99a-4477-bec1-a446149ec3f2.png&w=1280&q=85" alt="Analytics 2" className="sm:w-[55%] aspect-[900/600] rounded-xl sm:rounded-2xl object-cover" />
              </div>
            </div>

            {/* Desktop Grid */}
            <div className="hidden lg:grid grid-cols-[26%_1fr_48%] items-end gap-6 xl:gap-8">
              <img src="https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260516_090123_74be96d4-9c1b-40cf-932a-96f4f4babed3.png&w=1280&q=85" alt="Analytics 1" className="w-full aspect-[438/346] rounded-2xl object-cover self-end" />
              <div className="self-start flex flex-col justify-end items-end text-right h-full pb-8">
                <p className="text-[16px] xl:text-[18px] leading-[1.65] font-medium text-gray-900 whitespace-nowrap mb-6">
                  Through research, creative thinking and <br/> iteration we help growing brands realize <br/> their digital full potential.
                </p>
                <a href="http://localhost:8000/login" className="group flex items-center bg-[#F26522] hover:bg-[#e05a1a] text-white text-[14px] rounded-full pl-6 pr-2 py-2 gap-3 transition-colors duration-300">
                  <div className="overflow-hidden h-[20px] relative w-auto min-w-[130px] flex items-center">
                     <div className="flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                       <span className="h-[20px] flex items-center">Explore Dashboard</span>
                       <span className="h-[20px] flex items-center">Explore Dashboard</span>
                     </div>
                  </div>
                  <div className="flex items-center justify-center w-8 h-8 bg-white rounded-full transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-rotate-45">
                    <ArrowRight size={14} className="text-[#F26522]" />
                  </div>
                </a>
              </div>
              <img src="https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260516_090133_c157d30b-a99a-4477-bec1-a446149ec3f2.png&w=1280&q=85" alt="Analytics 2" className="w-full aspect-[3/2] rounded-2xl object-cover self-end" />
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 3: CASE STUDIES
          ========================================================================= */}
      <section className="bg-[#F5F5F5] pt-16 sm:pt-20 lg:pt-28 pb-16 sm:pb-20 lg:pb-28 relative z-20">
        <div className="mx-auto max-w-[1440px]">
          <div className="px-5 sm:px-8 lg:px-12 flex items-center gap-3 mb-6 sm:mb-8">
            <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-gray-900 text-white text-[11px] sm:text-[12px] font-semibold flex items-center justify-center">2</div>
            <div className="text-[12px] sm:text-[13px] font-medium border border-gray-300 rounded-full px-3 sm:px-4 py-1 sm:py-1.5">Featured client work</div>
          </div>

          <div className="px-5 sm:px-8 lg:px-12">
            <h2 className="text-[clamp(1.75rem,7vw,4.2rem)] sm:text-[clamp(2.5rem,5vw,4.2rem)] font-medium leading-[1.08] tracking-[-0.03em] text-gray-900 mb-10 sm:mb-14 lg:mb-16">
              Our projects
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6 lg:gap-7 px-5 sm:px-8 lg:px-12">
            {/* Card 1 */}
            <div>
              <div className="aspect-[329/246] rounded-2xl overflow-hidden bg-[#1a1d2e] group cursor-pointer relative">
                <video src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260516_122702_390f5305-8719-41d5-ae80-d23ab3796c28.mp4" autoPlay muted loop playsInline className="w-full h-full object-cover" />
                <a href="http://localhost:8000/login" className="absolute bottom-4 left-4 h-9 w-9 bg-white rounded-full flex items-center overflow-hidden transition-all duration-300 ease-in-out group-hover:w-[148px]">
                  <div className="flex-shrink-0 w-9 h-9 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-900 transition-transform duration-300 -rotate-45 group-hover:rotate-0">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                  </div>
                  <span className="text-[13px] font-medium text-gray-900 opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-100 whitespace-nowrap pr-4">Learn more</span>
                </a>
              </div>
              <div className="mt-4 text-[13px] sm:text-[14px] text-gray-600 leading-relaxed">
                An interactive dashboard driving real-time mutual fund engagement and performance tracking.
              </div>
              <div className="mt-1 text-[14px] sm:text-[15px] font-semibold text-gray-900">
                Live NAV Tracking
              </div>
            </div>

            {/* Card 2 */}
            <div>
              <div className="aspect-square rounded-2xl overflow-hidden bg-[#6b6b6b] group cursor-pointer relative">
                <video src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260516_123323_f909c2b8-ff6c-4edf-882b-8ebcdbe389b5.mp4" autoPlay muted loop playsInline className="w-full h-full object-cover" />
                <a href="http://localhost:8000/login" className="absolute bottom-4 left-4 h-9 w-9 bg-gray-900 rounded-full flex items-center overflow-hidden transition-all duration-300 ease-in-out group-hover:w-[168px]">
                  <div className="flex-shrink-0 w-9 h-9 flex items-center justify-center">
                    <ArrowRight size={14} className="text-white transition-transform duration-300 -rotate-45 group-hover:rotate-0" />
                  </div>
                  <span className="text-[13px] font-medium text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-100 whitespace-nowrap pr-4">View case study</span>
                </a>
              </div>
              <div className="mt-4 text-[13px] sm:text-[14px] text-gray-600 leading-relaxed">
                Transforming complex market data into a conversion-focused investment experience.
              </div>
              <div className="mt-1 text-[14px] sm:text-[15px] font-semibold text-gray-900">
                Advanced Analytics
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}

export default App;
