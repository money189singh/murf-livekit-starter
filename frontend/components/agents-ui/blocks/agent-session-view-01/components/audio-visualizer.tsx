'use client';

import React from 'react';
import { type MotionProps, motion } from 'motion/react';
import { useVoiceAssistant } from '@livekit/components-react';

import { AgentAudioVisualizerAura } from '@/components/agents-ui/agent-audio-visualizer-aura';
import { AgentAudioVisualizerBar } from '@/components/agents-ui/agent-audio-visualizer-bar';
import { AgentAudioVisualizerGrid } from '@/components/agents-ui/agent-audio-visualizer-grid';
import { AgentAudioVisualizerRadial } from '@/components/agents-ui/agent-audio-visualizer-radial';
import { AgentAudioVisualizerWave } from '@/components/agents-ui/agent-audio-visualizer-wave';

import { cn } from '@/lib/shadcn/utils';

const MotionAura = motion.create(AgentAudioVisualizerAura);
const MotionBar = motion.create(AgentAudioVisualizerBar);
const MotionGrid = motion.create(AgentAudioVisualizerGrid);
const MotionRadial = motion.create(AgentAudioVisualizerRadial);
const MotionWave = motion.create(AgentAudioVisualizerWave);

interface AudioVisualizerProps extends MotionProps {
  isChatOpen: boolean;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';

  audioVisualizerColor?: `#${string}`;

  audioVisualizerColorShift?: number;

  audioVisualizerWaveLineWidth?: number;

  audioVisualizerGridRowCount?: number;

  audioVisualizerGridColumnCount?: number;

  audioVisualizerRadialBarCount?: number;

  audioVisualizerRadialRadius?: number;

  audioVisualizerBarCount?: number;

  className?: string;
}

export function AudioVisualizer({
  audioVisualizerType = 'aura',

  audioVisualizerColor = '#00A878',

  audioVisualizerColorShift = 0.15,

  audioVisualizerBarCount = 5,

  audioVisualizerRadialRadius = 100,

  audioVisualizerRadialBarCount = 25,

  audioVisualizerGridRowCount = 15,

  audioVisualizerGridColumnCount = 15,

  audioVisualizerWaveLineWidth = 3,

  isChatOpen,

  className,

  ...props
}: AudioVisualizerProps) {
  const { state, audioTrack } = useVoiceAssistant();

  const sizeClass = cn(
    'size-[250px] md:size-[330px]',
    className
  );

  switch (audioVisualizerType) {
    case 'aura':
      return (
        <MotionAura
          state={state}
          audioTrack={audioTrack}
          color={audioVisualizerColor}
          colorShift={audioVisualizerColorShift}
          className={sizeClass}
          {...props}
        />
      );

    case 'wave':
      return (
        <motion.div
          className={cn(
            'flex items-center justify-center',
            className
          )}
          {...props}
        >
          <MotionWave
            state={state}
            audioTrack={audioTrack}
            color={audioVisualizerColor}
            colorShift={audioVisualizerColorShift}
            lineWidth={
              isChatOpen
                ? audioVisualizerWaveLineWidth * 2
                : audioVisualizerWaveLineWidth
            }
            className="size-[250px] md:size-[330px]"
          />
        </motion.div>
      );

    case 'grid': {
      const totalCount =
        audioVisualizerGridRowCount *
        audioVisualizerGridColumnCount;

      let size: 'icon' | 'sm' | 'md' | 'lg' | 'xl' = 'sm';

      if (totalCount < 100) {
        size = 'xl';
      } else if (totalCount < 200) {
        size = 'lg';
      } else if (totalCount < 300) {
        size = 'md';
      }

      return (
        <MotionGrid
          size={size}
          state={state}
          color={audioVisualizerColor}
          audioTrack={audioTrack}
          rowCount={audioVisualizerGridRowCount}
          columnCount={audioVisualizerGridColumnCount}
          radius={Math.round(
            Math.min(
              audioVisualizerGridRowCount,
              audioVisualizerGridColumnCount
            ) / 4
          )}
          className={cn(
            'size-[280px] gap-0 p-8 *:place-self-center md:size-[340px]',
            className
          )}
          {...props}
        />
      );
    }

    case 'radial':
      return (
        <motion.div
          className={cn(
            'flex items-center justify-center',
            className
          )}
          {...props}
        >
          <MotionRadial
            size="xl"
            state={state}
            color={audioVisualizerColor}
            audioTrack={audioTrack}
            radius={audioVisualizerRadialRadius}
            barCount={audioVisualizerRadialBarCount}
            className="size-[300px] md:size-[360px]"
          />
        </motion.div>
      );

    case 'bar':
    default: {
      let size: 'icon' | 'sm' | 'md' | 'lg' | 'xl' = 'xl';

      let sizedClassName = cn(
        'size-[250px] md:size-[330px]',
        className
      );

      if (audioVisualizerBarCount <= 5) {
        size = 'xl';

        sizedClassName = cn(
          'size-[300px] md:size-[340px] gap-3 *:min-h-[50px] *:w-[42px]',
          className
        );
      } else if (audioVisualizerBarCount <= 10) {
        size = 'lg';
      } else if (audioVisualizerBarCount <= 15) {
        size = 'md';
      } else if (audioVisualizerBarCount <= 30) {
        size = 'sm';
      }

      return (
        <MotionBar
          size={size}
          state={state}
          color={audioVisualizerColor}
          audioTrack={audioTrack}
          barCount={audioVisualizerBarCount}
          className={sizedClassName}
          {...props}
        >
          <span className="min-h-2.5 w-2.5 rounded-full bg-current/10 transition-all duration-300 data-[lk-highlighted=true]:bg-current" />
        </MotionBar>
      );
    }
  }
}
