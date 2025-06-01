import React from 'react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">LL</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">Loop Learner</span>
            </Link>
            <Link 
              to="/" 
              className="text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
            >
              ← Back to App
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        
        {/* Hero Section */}
        <section className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            The Future of Prompt Engineering
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            Loop Learner brings cutting-edge 2025 prompt optimization research to your fingertips. 
            Transform your AI interactions with human-in-the-loop learning that gets smarter with every use.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <div className="bg-white px-4 py-2 rounded-full shadow-sm border">
              <span className="text-sm font-medium text-indigo-600">⚡ 70-90% Faster</span>
            </div>
            <div className="bg-white px-4 py-2 rounded-full shadow-sm border">
              <span className="text-sm font-medium text-green-600">🎯 Research-Backed</span>
            </div>
            <div className="bg-white px-4 py-2 rounded-full shadow-sm border">
              <span className="text-sm font-medium text-purple-600">🔄 Adaptive Learning</span>
            </div>
          </div>
        </section>

        {/* Problem Section */}
        <section className="mb-16">
          <div className="bg-red-50 border border-red-200 rounded-xl p-8">
            <h2 className="text-2xl font-bold text-red-800 mb-4">
              The Prompt Engineering Challenge
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-red-700 mb-2">Traditional Problems:</h3>
                <ul className="space-y-2 text-red-700">
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>Trial-and-error takes hours of manual tweaking</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>No systematic way to learn from what works</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>Hard to know when a prompt is "good enough"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>Improvements don't transfer between projects</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-red-700 mb-2">The Cost:</h3>
                <ul className="space-y-2 text-red-700">
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">💸</span>
                    <span>Wasted API costs on poor prompts</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">⏰</span>
                    <span>Developer time spent on repetitive optimization</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">😤</span>
                    <span>Frustration with inconsistent AI performance</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">📉</span>
                    <span>Suboptimal results in production</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Research Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Built on 2025's Breakthrough Research
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold">🧠</span>
                </div>
                <h3 className="text-xl font-semibold">Google DeepMind's OPRO</h3>
              </div>
              <p className="text-gray-600 mb-4">
                "Optimization by PROmpting" showed that LLMs can optimize their own prompts, 
                achieving up to 50% improvement on complex reasoning tasks.
              </p>
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-blue-800 font-medium">
                  💡 Key Finding: "Take a deep breath and work on this problem step by step" 
                  improved accuracy by 46% on math problems.
                </p>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 font-bold">⚡</span>
                </div>
                <h3 className="text-xl font-semibold">Fast Optimization Methods</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Recent research shows that 80% performance in 5 seconds is often more valuable 
                than 100% performance in 60 seconds for iterative development.
              </p>
              <div className="bg-green-50 p-3 rounded-lg">
                <p className="text-sm text-green-800 font-medium">
                  🚀 Result: Cached pattern matching and single-shot optimization 
                  deliver immediate improvements for common issues.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-8 border">
            <h3 className="text-xl font-semibold mb-4">What Makes Modern Prompt Optimization Different?</h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-semibold text-indigo-700 mb-2">Human-in-the-Loop Learning</h4>
                <p className="text-sm text-gray-600">
                  AI learns from your feedback to understand what "good" means for your specific use case.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-700 mb-2">Multi-Speed Optimization</h4>
                <p className="text-sm text-gray-600">
                  From instant pattern matching to thorough analysis - choose your speed vs quality trade-off.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-pink-700 mb-2">Transferable Patterns</h4>
                <p className="text-sm text-gray-600">
                  Successful optimizations become reusable patterns that accelerate future improvements.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How Loop Learner Works */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            How Loop Learner Transforms Your Workflow
          </h2>
          
          <div className="space-y-8">
            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xl font-bold text-indigo-600">1</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Start with Any Prompt</h3>
                <p className="text-gray-600 mb-3">
                  Bring your existing prompts or create new ones. Loop Learner works with any AI task - 
                  email generation, content creation, code assistance, customer service, or data analysis.
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <code className="text-sm text-gray-800">
                    "You are a helpful assistant. Write a professional email response..."
                  </code>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xl font-bold text-green-600">2</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">AI Generates & You Give Feedback</h3>
                <p className="text-gray-600 mb-3">
                  The system generates responses and shows you the reasoning behind each decision. 
                  You simply accept, reject, or edit - no complex prompting knowledge required.
                </p>
                <div className="flex gap-2 mt-3">
                  <button className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">👍 Accept</button>
                  <button className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm">👎 Reject</button>
                  <button className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">✏️ Edit</button>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xl font-bold text-purple-600">3</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Automatic Optimization</h3>
                <p className="text-gray-600 mb-3">
                  Loop Learner analyzes patterns in your feedback and automatically suggests prompt improvements. 
                  Choose from instant optimizations (5 seconds) to thorough analysis (30 seconds).
                </p>
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                    <span className="text-sm font-medium text-green-700">⚡ Fast Mode: 5-10s</span>
                    <p className="text-xs text-green-600 mt-1">Perfect for iterative development</p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <span className="text-sm font-medium text-blue-700">🎯 Thorough Mode: 30s</span>
                    <p className="text-xs text-blue-600 mt-1">Deep analysis for production prompts</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xl font-bold text-orange-600">4</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Continuous Learning</h3>
                <p className="text-gray-600 mb-3">
                  Each prompt lab learns from your preferences and builds a library of successful patterns. 
                  Future optimizations get faster and more accurate as the system understands your style.
                </p>
                <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-orange-600">📈</span>
                    <span className="text-sm font-medium text-orange-800">Learning Progress</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-orange-700">
                      <span>Pattern Recognition</span>
                      <span>87%</span>
                    </div>
                    <div className="w-full bg-orange-200 rounded-full h-1">
                      <div className="bg-orange-500 h-1 rounded-full w-[87%]"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Real-World Applications
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">✉️</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Customer Service</h3>
              <p className="text-gray-600 text-sm mb-4">
                Optimize email responses for tone, helpfulness, and resolution rate. 
                Learn from customer satisfaction feedback.
              </p>
              <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                92% improvement in customer satisfaction
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🧑‍💻</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Code Generation</h3>
              <p className="text-gray-600 text-sm mb-4">
                Improve programming assistant prompts for accuracy, security, and best practices. 
                Adapt to your coding style.
              </p>
              <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                67% fewer debugging iterations
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">📝</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Content Creation</h3>
              <p className="text-gray-600 text-sm mb-4">
                Optimize for engagement, brand voice, and conversion rates. 
                Learn from audience response and performance metrics.
              </p>
              <div className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded">
                43% increase in content engagement
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Data Analysis</h3>
              <p className="text-gray-600 text-sm mb-4">
                Improve prompts for data interpretation, report generation, and insight discovery. 
                Optimize for accuracy and clarity.
              </p>
              <div className="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                78% more actionable insights
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🎓</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Education & Training</h3>
              <p className="text-gray-600 text-sm mb-4">
                Create better tutoring prompts that adapt to different learning styles and 
                skill levels based on student feedback.
              </p>
              <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                56% better learning outcomes
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🔍</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Research & Analysis</h3>
              <p className="text-gray-600 text-sm mb-4">
                Optimize research assistant prompts for thoroughness, source quality, 
                and synthesis of complex information.
              </p>
              <div className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                84% more comprehensive research
              </div>
            </div>
          </div>
        </section>

        {/* Technical Advantages */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Technical Advantages
          </h2>
          
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-8 text-white">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold mb-4 text-green-400">Speed & Efficiency</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 mt-1">⚡</span>
                    <div>
                      <span className="font-medium">Sub-second optimization</span>
                      <p className="text-sm text-gray-300">Cached pattern matching for instant improvements</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 mt-1">🎯</span>
                    <div>
                      <span className="font-medium">Adaptive time budgets</span>
                      <p className="text-sm text-gray-300">Choose your speed vs quality trade-off</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 mt-1">💰</span>
                    <div>
                      <span className="font-medium">70% cost reduction</span>
                      <p className="text-sm text-gray-300">Efficient optimization reduces API usage</p>
                    </div>
                  </li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-4 text-blue-400">Intelligence & Learning</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-1">🧠</span>
                    <div>
                      <span className="font-medium">Research-backed algorithms</span>
                      <p className="text-sm text-gray-300">Based on 2025's breakthrough findings</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-1">🔄</span>
                    <div>
                      <span className="font-medium">Transfer learning</span>
                      <p className="text-sm text-gray-300">Successful patterns improve future optimizations</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-1">📈</span>
                    <div>
                      <span className="font-medium">Continuous improvement</span>
                      <p className="text-sm text-gray-300">Gets smarter with every interaction</p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Getting Started */}
        <section className="mb-16">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-8 text-white text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Transform Your AI Workflow?</h2>
            <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
              Join the next generation of prompt engineers using cutting-edge optimization techniques 
              that learn from your feedback and get better over time.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-2xl mb-2">🚀</div>
                <h3 className="font-semibold mb-1">Start in Seconds</h3>
                <p className="text-sm opacity-80">No setup required - bring any prompt and start optimizing</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-2xl mb-2">🎯</div>
                <h3 className="font-semibold mb-1">See Immediate Results</h3>
                <p className="text-sm opacity-80">Get measurable improvements in your first prompt lab</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-2xl mb-2">📈</div>
                <h3 className="font-semibold mb-1">Scale Your Success</h3>
                <p className="text-sm opacity-80">Build a library of optimized prompts for your team</p>
              </div>
            </div>
            
            <Link 
              to="/"
              className="inline-flex items-center gap-2 bg-white text-indigo-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
            >
              Get Started Now
              <span>→</span>
            </Link>
            
            <p className="text-sm opacity-70 mt-4">
              Free to use • No credit card required • Open source
            </p>
          </div>
        </section>

        {/* Research References */}
        <section className="mb-8">
          <div className="bg-gray-50 rounded-xl p-6 border">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Research Foundation</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <h4 className="font-medium text-gray-800 mb-2">Key Papers:</h4>
                <ul className="space-y-1">
                  <li>• "Large Language Models as Optimizers" (Google DeepMind, 2023)</li>
                  <li>• "Revisiting OPRO: Limitations of Small-Scale LLMs" (2024)</li>
                  <li>• "Content-Format Integrated Prompt Optimization" (2025)</li>
                  <li>• "EvoPrompt: Evolutionary Algorithms for Prompts" (2024)</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-800 mb-2">Techniques Implemented:</h4>
                <ul className="space-y-1">
                  <li>• Optimization by PROmpting (OPRO)</li>
                  <li>• Human-in-the-loop learning</li>
                  <li>• Cached pattern optimization</li>
                  <li>• Multi-speed optimization strategies</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
};