'use client';

import { Button } from '@/components/ui/button';
import { HeartPulse, Mic } from 'lucide-react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ...props
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      {...props}
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-teal-50 px-6 py-12"
    >
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-emerald-200/30 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-teal-200/30 blur-3xl" />
      </div>

      {/* Main content */}
      <main className="relative z-10 flex w-full max-w-xl flex-col items-center text-center">
        {/* Logo / icon */}
        <div className="mb-7 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 shadow-sm ring-8 ring-emerald-50">
          <HeartPulse
            className="h-10 w-10 text-emerald-600"
            strokeWidth={1.8}
          />
        </div>

        {/* Brand */}
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Health Access
        </h1>

        <p className="mt-3 text-lg font-medium text-slate-600">
          Your voice healthcare assistant
        </p>

        {/* Description */}
        <p className="mt-5 max-w-md text-sm leading-6 text-slate-500 sm:text-base">
          Get general health information and guidance through a natural voice
          conversation.
        </p>

        {/* Language support */}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          <span className="rounded-full bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm ring-1 ring-slate-200">
            🇮🇳 Hindi
          </span>

          <span className="rounded-full bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm ring-1 ring-slate-200">
            Hinglish
          </span>

          <span className="rounded-full bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm ring-1 ring-slate-200">
            English
          </span>
        </div>

        {/* Microphone button */}
        <div className="relative mt-10">
          <div className="absolute inset-0 animate-ping rounded-full bg-emerald-200 opacity-40" />

          <Button
            size="lg"
            onClick={onStartCall}
            className="relative flex h-24 w-24 rounded-full bg-emerald-600 p-0 shadow-xl shadow-emerald-600/20 transition-all duration-200 hover:scale-105 hover:bg-emerald-700 active:scale-95"
            aria-label="Start talking"
          >
            <Mic className="h-10 w-10 text-white" strokeWidth={2} />
          </Button>
        </div>

        {/* Start text */}
        <p className="mt-6 text-lg font-semibold text-slate-800">
          Ready to talk?
        </p>

        <p className="mt-1 text-sm text-slate-500">
          Tap the microphone to start
        </p>

        {/* Main button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-6 h-12 w-64 rounded-full bg-emerald-600 font-semibold shadow-lg shadow-emerald-600/20 hover:bg-emerald-700"
        >
          <Mic className="mr-2 h-5 w-5" />
          {startButtonText || 'Start Talking'}
        </Button>

        {/* Safety information */}
        <div className="mt-8 max-w-md rounded-2xl border border-emerald-100 bg-white/80 px-5 py-4 shadow-sm backdrop-blur-sm">
          <p className="text-xs leading-5 text-slate-500 sm:text-sm">
            Health Access provides general health information only. It does
            not diagnose conditions, prescribe medication, or replace a
            healthcare professional.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="absolute bottom-5 left-0 w-full px-6 text-center">
        <p className="text-xs text-slate-400">
          Health Access • Voice AI for easier healthcare access
        </p>
      </footer>
    </div>
  );
};
