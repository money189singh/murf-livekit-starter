'use client';

import React, { useMemo } from 'react';
import { Track } from 'livekit-client';
import { motion } from 'motion/react';

import {
  type TrackReference,
  VideoTrack,
  useLocalParticipant,
  useTracks,
} from '@livekit/components-react';

import { cn } from '@/lib/shadcn/utils';

import { AudioVisualizer } from './audio-visualizer';

interface TileLayoutProps {
  chatOpen: boolean;

  audioVisualizerType?:
    | 'bar'
    | 'wave'
    | 'grid'
    | 'radial'
    | 'aura';

  audioVisualizerColor?: `#${string}`;

  audioVisualizerColorShift?: number;

  audioVisualizerWaveLineWidth?: number;

  audioVisualizerGridRowCount?: number;

  audioVisualizerGridColumnCount?: number;

  audioVisualizerRadialBarCount?: number;

  audioVisualizerRadialRadius?: number;

  audioVisualizerBarCount?: number;
}

export function useLocalTrackRef(
  source: Track.Source
) {
  const { localParticipant } =
    useLocalParticipant();

  const publication =
    localParticipant.getTrackPublication(source);

  const trackRef = useMemo<
    TrackReference | undefined
  >(
    () =>
      publication
        ? {
            source,
            participant: localParticipant,
            publication,
          }
        : undefined,
    [
      source,
      publication,
      localParticipant,
    ]
  );

  return trackRef;
}

export function TileLayout({
  chatOpen,
  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerWaveLineWidth,
}: TileLayoutProps) {
  const [screenShareTrack] = useTracks([
    Track.Source.ScreenShare,
  ]);

  const cameraTrack =
    useLocalTrackRef(Track.Source.Camera);

  const isCameraEnabled =
    cameraTrack &&
    !cameraTrack.publication.isMuted;

  const isScreenShareEnabled =
    screenShareTrack &&
    !screenShareTrack.publication.isMuted;

  const hasSecondTile =
    isCameraEnabled || isScreenShareEnabled;

  return (
    <div className="relative flex size-full items-center justify-center">
      {/* Main voice assistant */}
      <motion.div
        layout
        initial={{
          opacity: 0,
          scale: 0.85,
        }}
        animate={{
          opacity: 1,
          scale: chatOpen ? 0.72 : 1,
        }}
        transition={{
          type: 'spring',
          stiffness: 180,
          damping: 22,
        }}
        className={cn(
          'relative flex items-center justify-center',
          chatOpen && 'origin-center'
        )}
      >
        {/* Outer glow */}
        <motion.div
          animate={{
            scale: [1, 1.06, 1],
            opacity: [0.25, 0.4, 0.25],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute size-[260px] rounded-full bg-emerald-400/10 blur-2xl md:size-[330px]"
        />

        {/* Visualizer */}
        <div className="relative z-10">
          <AudioVisualizer
            isChatOpen={chatOpen}
            audioVisualizerType={
              audioVisualizerType
            }
            audioVisualizerColor={
              audioVisualizerColor
            }
            audioVisualizerColorShift={
              audioVisualizerColorShift
            }
            audioVisualizerBarCount={
              audioVisualizerBarCount
            }
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

        {/* Center icon */}
        <div className="pointer-events-none absolute z-20 flex size-20 items-center justify-center rounded-full border border-white/80 bg-white/90 shadow-xl shadow-emerald-900/10 backdrop-blur-md">
          <div className="flex size-12 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/25">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              className="size-6"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path
                d="M12 14.5a3.5 3.5 0 0 0 3.5-3.5V6a3.5 3.5 0 0 0-7 0v5a3.5 3.5 0 0 0 3.5 3.5Z"
                strokeLinecap="round"
              />

              <path
                d="M19 10.5a7 7 0 0 1-14 0M12 17.5V21M8.5 21h7"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>
      </motion.div>

      {/* Camera / screen share preview */}
      {hasSecondTile && (
        <motion.div
          initial={{
            opacity: 0,
            scale: 0.8,
            x: 30,
          }}
          animate={{
            opacity: 1,
            scale: 1,
            x: 0,
          }}
          exit={{
            opacity: 0,
            scale: 0.8,
          }}
          className="absolute bottom-2 right-2 size-20 overflow-hidden rounded-2xl border-2 border-white bg-white shadow-xl md:bottom-5 md:right-5 md:size-24"
        >
          <VideoTrack
            trackRef={
              cameraTrack ||
              screenShareTrack
            }
            width={
              (
                cameraTrack ||
                screenShareTrack
              )?.publication.dimensions
                ?.width ?? 0
            }
            height={
              (
                cameraTrack ||
                screenShareTrack
              )?.publication.dimensions
                ?.height ?? 0
            }
            className="size-full object-cover"
          />
        </motion.div>
      )}
    </div>
  );
}
