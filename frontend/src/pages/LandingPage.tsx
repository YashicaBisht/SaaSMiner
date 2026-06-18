import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Code, Shield, Cpu, Layers, DollarSign, FileText } from 'lucide-react'

const LandingPage: React.FC = () => {
  return (
    <div className="relative min-h-screen bg-background text-gray-100 overflow-hidden flex flex-col justify-between">
      {/* Background glowing effects */}
      <div className="glowing-orb top-[-200px] left-[-100px]"></div>
      <div className="glowing-orb-emerald bottom-[-150px] right-[-100px]"></div>

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none"></div>

      {/* Top Navigation */}
      <header className="relative z-10 max-w-7xl mx-auto w-full px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">SaaSMiner AI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/auth?mode=login" className="text-sm font-semibold text-gray-300 hover:text-white transition-colors">Sign In</Link>
          <Link 
            to="/auth?mode=signup" 
            className="px-4 py-2 text-sm font-bold bg-primary-600 hover:bg-primary-700 text-white rounded-xl shadow-lg shadow-primary-500/10 hover:shadow-primary-500/25 transition-all flex items-center gap-1"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 max-w-7xl mx-auto w-full px-6 py-12 flex-1 flex flex-col lg:flex-row items-center justify-center gap-16">
        {/* Left Side: Copy */}
        <div className="flex-1 text-center lg:text-left space-y-8 max-w-2xl">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-950/60 border border-primary-800/50 text-primary-300 text-xs font-semibold"
          >
            <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse"></span>
            100% Private, Local AST Analytics
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-none"
          >
            Turn Software Projects <br />
            into <span className="gradient-text">Product Opportunities</span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base sm:text-lg text-gray-400 font-medium leading-relaxed"
          >
            Upload any codebase ZIP file or point to a public GitHub URL. Instantly detect isolated microservice splits, map modular API tables, extract SaaS business opportunities, and generate printable executive dossiers. All completely offline inside VS Code.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4"
          >
            <Link 
              to="/auth?mode=signup" 
              className="w-full sm:w-auto px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-xl shadow-xl shadow-primary-500/20 hover:shadow-primary-500/35 transition-all flex items-center justify-center gap-2 group"
            >
              Analyze Project
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link 
              to="/auth?mode=login" 
              className="w-full sm:w-auto px-8 py-4 bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 text-gray-300 hover:text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
            >
              View Dashboard
            </Link>
          </motion.div>
        </div>

        {/* Right Side: Floating AI Orb Mockup */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="flex-1 relative w-full max-w-md lg:max-w-none flex items-center justify-center"
        >
          {/* Animated floating orb card container */}
          <div className="w-full aspect-[4/3] rounded-2xl glass-panel p-6 border border-gray-800/80 shadow-2xl flex flex-col justify-between overflow-hidden animate-float">
            {/* Window header */}
            <div className="flex items-center justify-between border-b border-gray-800/60 pb-4">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500/80"></span>
                <span className="w-3 h-3 rounded-full bg-green-500/80"></span>
              </div>
              <span className="text-xs text-gray-500 font-mono tracking-wider">SAASMINER_ENGINE</span>
            </div>

            {/* Glowing Orb Animation */}
            <div className="flex-1 flex items-center justify-center relative">
              <div className="absolute w-32 h-32 rounded-full bg-primary-600/30 filter blur-xl animate-pulse"></div>
              {/* Outer spinning ring */}
              <div className="absolute w-24 h-24 rounded-full border border-dashed border-primary-400/50 animate-spin-slow"></div>
              {/* Inner floating core */}
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-primary-400 to-indigo-600 shadow-lg shadow-primary-500/40 flex items-center justify-center">
                <Code className="w-6 h-6 text-white" />
              </div>
            </div>

            {/* Simulated Analysis output */}
            <div className="bg-gray-950/60 border border-gray-900 rounded-xl p-4 font-mono text-[11px] leading-relaxed space-y-1.5 text-gray-400">
              <p className="text-primary-400 font-semibold">&gt; Scanning directories...</p>
              <p>&gt; Found: 42 files, 8 db models, 15 API routes</p>
              <p>&gt; Domain match: <span className="text-emerald-400">Healthcare (94% confidence)</span></p>
              <p>&gt; Product Potential Score: <span className="text-primary-300 font-bold">91/100</span></p>
            </div>
          </div>
        </motion.div>
      </main>

        {/* Feature Cards Grid */}
        <section className="relative z-10 max-w-7xl mx-auto w-full px-6 py-20 border-t border-gray-900/60">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary-950/60 border border-primary-800/40 flex items-center justify-center text-primary-400 shadow-md">
                <Code className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg">Smart AST Scanner</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Runs native AST parsers and regex scanners to decode Python, JS/TS, Java, and Go structure models without compiling.</p>
            </div>

            <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-900/40 flex items-center justify-center text-emerald-400 shadow-md">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg">Microservice Blueprinting</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Reconstructs monolithic class bindings into decoupled microservice schemas with dedicated database mapping blueprints.</p>
            </div>

            <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-950/60 border border-indigo-900/40 flex items-center justify-center text-indigo-400 shadow-md">
                <DollarSign className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg">Go-To-Market Modeling</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Computes potential target sizing, ideal monetization models, and lists customer demographics to accelerate launching.</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="relative z-10 w-full px-6 py-8 border-t border-gray-950 text-center text-xs text-gray-500 font-medium">
          &copy; {new Date().getFullYear()} SaaSMiner AI. Designed for 100% private offline operation inside VS Code.
        </footer>
    </div>
  )
}

export default LandingPage
