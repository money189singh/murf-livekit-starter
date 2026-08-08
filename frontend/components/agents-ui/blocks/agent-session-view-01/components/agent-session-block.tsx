'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';

import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';

import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  className?: string;
}

function getAgentStatus(state: string | undefined) {
  switch (state) {
    case 'connecting':
      return {
        title: 'Connecting...',
        subtitle: 'Please wait while we connect you',
        dot: 'bg-amber-400',
        pulse: true,
      };

    case 'initializing':
      return {
        title: 'Getting ready...',
        subtitle: 'Your health assistant is preparing',
        dot: 'bg-amber-400',
        pulse: true,
      };

    case 'listening':
      return {
        title: 'Listening to you',
        subtitle: 'Speak naturally in Hindi, Hinglish, or English',
        dot: 'bg-emerald-500',
        pulse: true,
      };

    case 'thinking':
      return {
        title: 'Thinking...',
        subtitle: 'Give me a moment',
        dot: 'bg-blue-500',
        pulse: true,
      };

    case 'speaking':
      return {
        title: 'Health Access is speaking',
        subtitle: 'You can listen to the response',
        dot: 'bg-violet-500',
        pulse: true,
      };

    case 'failed':
      return {
        title: 'Something went wrong',
        subtitle: 'Please try connecting again',
        dot: 'bg-red-500',
        pulse: false,
      };

    default:
      return {
        title: 'Connected',
        subtitle: 'You can start speaking',
        dot: 'bg-emerald-500',
        pulse: true,
      };
  }
}

function StatusIndicator({
  state,
}: {
  state: string | undefined;
}) {
  const status = getAgentStatus(state);

  return (
    <div className="flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/80 px-4 py-2 shadow-sm backdrop-blur-md">
      <span className="relative flex size-2.5">
        {status.pulse && (
          <span
            className={cn(
              'absolute inline-flex size-full animate-ping rounded-full opacity-60',
              status.dot
            )}
          />
        )}

        <span
          className={cn(
            'relative inline-flex size-2.5 rounded-full',
            status.dot
          )}
        />
      </span>

      <span className="text-xs font-semibold text-slate-700">
        {status.title}
      </span>
    </div>
  );
}

function LanguageBadge() {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 text-[11px] font-medium text-slate-600 shadow-sm backdrop-blur-md">
      <span>हिंदी</span>
      <span className="text-slate-300">•</span>
      <span>Hinglish</span>
      <span className="text-slate-300">•</span>
      <span>English</span>
    </div>
  );
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
  isPreConnectBufferEnabled = true,

  audioVisualizerType = 'aura',
  audioVisualizerColor = '#059669',
  audioVisualizerColorShift = 0.15,
  audioVisualizerBarCount = 5,
  audioVisualizerGridRowCount = 15,
  audioVisualizerGridColumnCount = 15,
  audioVisualizerRadialBarCount = 25,
  audioVisualizerRadialRadius = 100,
  audioVisualizerWaveLineWidth = 3,

  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();

  const [chatOpen, setChatOpen] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement | null>(null);

  const status = getAgentStatus(agentState);

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop =
        scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section
      ref={ref}
      className={cn(
        'relative z-10 flex h-full min-h-screen w-full flex-col overflow-hidden',
        'bg-[#f5fbf8]',
        className
      )}
      {...props}
    >
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 size-[500px] rounded-full bg-emerald-200/20 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 size-[500px] rounded-full bg-teal-200/20 blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-20 flex items-center justify-between px-5 py-5 md:px-10 md:py-7">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 shadow-sm">
            <span className="text-xl">♥</span>
          </div>

          <div>
            <h1 className="text-sm font-bold tracking-tight text-slate-900 md:text-base">
              Health Access
            </h1>

            <p className="text-[11px] text-slate-500 md:text-xs">
              Voice healthcare assistant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <LanguageBadge />
          <StatusIndicator state={agentState} />
        </div>
      </header>

      {/* Main */}
      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <div className="relative flex min-h-0 flex-1 items-center justify-center px-4">
          {/* Conversation */}
          <AnimatePresence mode="wait">
            {chatOpen ? (
              <motion.div
                key="chat"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 15 }}
                transition={{ duration: 0.25 }}
                className="absolute inset-x-4 top-2 bottom-2 mx-auto flex max-w-3xl flex-col overflow-hidden rounded-3xl border border-slate-200/80 bg-white/90 shadow-xl shadow-emerald-900/5 backdrop-blur-xl md:inset-x-10 md:top-5 md:bottom-5"
              >
                <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">
                      Conversation
                    </h2>

                    <p className="text-xs text-slate-500">
                      Your conversation stays in this session
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setChatOpen(false)}
                    className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
                  >
                    Close
                  </button>
                </div>

                <div
                  ref={scrollAreaRef}
                  className="min-h-0 flex-1 overflow-y-auto"
                >
                  <AgentChatTranscript
                    agentState={agentState}
                    messages={messages}
                    className="mx-auto w-full max-w-2xl px-3 pb-8 pt-5 [&_.is-user>div]:rounded-[20px] [&>div>div]:px-4 md:[&>div>div]:px-6"
                  />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="voice"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.3 }}
                className="flex w-full max-w-2xl flex-col items-center justify-center"
              >
                {/* Visualizer container */}
                <div className="relative flex size-[280px] items-center justify-center md:size-[390px]">
                  <div className="absolute size-[230px] rounded-full bg-emerald-100/50 blur-2xl md:size-[320px]" />

                  <div className="relative flex size-[220px] items-center justify-center rounded-full border border-emerald-100 bg-white/80 shadow-xl shadow-emerald-900/10 backdrop-blur-xl md:size-[280px]">
                    <TileLayout
                      chatOpen={false}
                      audioVisualizerType={audioVisualizerType}
                      audioVisualizerColor={audioVisualizerColor}
                      audioVisualizerColorShift={audioVisualizerColorShift}
                      audioVisualizerBarCount={audioVisualizerBarCount}
                      audioVisualizerRadialBarCount={
                        audioVisualizerRadialBarCount
                      }
                      audioVisualizerRadialRadius={
                        audioVisualizerRadialRadius
                      }
                      audioVisualizerGridRowCount={
                        audioVisualizerGridRowCount
                      }
                      audioVisualizerGridColumnCount={
                        audioVisualizerGridColumnCount
                      }
                      audioVisualizerWaveLineWidth={
                        audioVisualizerWaveLineWidth
                      }
                    />
                  </div>

                  {/* Decorative rings */}
                  <div className="absolute size-[245px] rounded-full border border-emerald-200/50 md:size-[310px]" />
                  <div className="absolute size-[275px] rounded-full border border-emerald-100/40 md:size-[350px]" />
                </div>

                {/* Status */}
                <div className="mt-2 text-center">
                  <motion.h2
                    key={status.title}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-xl font-bold tracking-tight text-slate-900 md:text-2xl"
                  >
                    {status.title}
                  </motion.h2>

                  <motion.p
                    key={status.subtitle}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-2 px-4 text-sm text-slate-500 md:text-base"
                  >
                    {status.subtitle}
                  </motion.p>
                </div>

                {/* Helpful language text */}
                <div className="mt-5 rounded-2xl border border-emerald-100 bg-white/70 px-5 py-3 text-center shadow-sm">
                  <p className="text-xs font-medium text-slate-600">
                    आप हिंदी में बात कर सकते हैं
                  </p>

                  <p className="mt-0.5 text-[11px] text-slate-400">
                    You can speak naturally in Hindi or Hinglish
                  </p>
                </div>

                {/* Pre-connect hint */}
                {isPreConnectBufferEnabled &&
                  messages.length === 0 &&
                  preConnectMessage && (
                    <p className="mt-4 text-center text-xs text-slate-400">
                      {preConnectMessage}
                    </p>
                  )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom controls */}
        <div className="relative z-30 px-4 pb-5 md:px-8 md:pb-8">
          <div className="mx-auto max-w-2xl rounded-3xl border border-white/80 bg-white/90 p-3 shadow-xl shadow-slate-900/5 backdrop-blur-xl">
            <AgentControlBar
              variant="livekit"
              controls={controls}
              isChatOpen={chatOpen}
              isConnected={session.isConnected}
              onDisconnect={session.end}
              onIsChatOpenChange={setChatOpen}
            />
          </div>

          {/* Disclaimer */}
          <div className="mx-auto mt-3 max-w-2xl text-center">
            <p className="text-[10px] leading-4 text-slate-400 md:text-[11px]">
              Health Access provides general health information only.
              It does not diagnose conditions, prescribe medication, or
              replace a healthcare professional.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
