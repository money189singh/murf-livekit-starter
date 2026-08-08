'use client';

import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';

import type { AppConfig } from '@/app-config';

import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({
  appConfig,
}: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();

  return (
    <AnimatePresence mode="wait">
      {/* Welcome / Ready screen */}
      {!isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={start}
        />
      )}

      {/* Connected voice assistant */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}

          supportsChatInput={appConfig.supportsChatInput}

          // Voice healthcare assistant doesn't need camera
          supportsVideoInput={false}

          // Voice healthcare assistant doesn't need screen sharing
          supportsScreenShare={false}

          isPreConnectBufferEnabled={
            appConfig.isPreConnectBufferEnabled
          }

          // Health Access visual style
          audioVisualizerType="aura"
          audioVisualizerColor="#00A878"
          audioVisualizerColorShift={0.15}

          audioVisualizerBarCount={5}
          audioVisualizerGridRowCount={15}
          audioVisualizerGridColumnCount={15}
          audioVisualizerRadialBarCount={25}
          audioVisualizerRadialRadius={100}
          audioVisualizerWaveLineWidth={3}

          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
