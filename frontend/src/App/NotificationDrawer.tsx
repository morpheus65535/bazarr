import { FunctionComponent, useState } from "react";
import TimeAgo from "react-timeago";
import {
  ActionIcon,
  Card,
  Collapse,
  Drawer,
  Group,
  Loader,
  Menu,
  RingProgress,
  Stack,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
import {
  faChevronDown,
  faChevronUp,
  faEllipsis,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSystemJobs } from "@/apis/hooks";
import Jobs = System.Jobs;
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startCase } from "lodash";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import classes from "./NotificationDrawer.module.css";

interface NotificationDrawerProps {
  opened: boolean;
  onClose: () => void;
}

const NotificationDrawer: FunctionComponent<NotificationDrawerProps> = ({
  opened,
  onClose,
}) => {
  const {
    data: jobs,
    isLoading: jobsLoading,
    error: jobsError,
  } = useSystemJobs();
  const client = useQueryClient();
  const { mutate: deleteJob, isPending: isCancelling } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Jobs, "delete"],
    mutationFn: (id: number) => api.system.deleteJobs(id),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Jobs],
      });
    },
  });

  const [collapsedSections, setCollapsedSections] = useState<
    Record<string, boolean>
  >({
    running: false,
    pending: false,
    completed: false,
  });

  const toggleSection = (section: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title="Jobs Manager"
      position="right"
      size="lg"
      overlayProps={{ opacity: 0.35, blur: 2 }}
    >
      {jobsLoading && (
        <Group justify="center" p="md">
          <Loader size="sm" />
          <Text size="sm">Loading jobs…</Text>
        </Group>
      )}

      {!jobsLoading && jobsError && (
        <Card withBorder padding="md" radius="sm">
          <Text c="red.6" size="sm">
            Failed to load jobs.
          </Text>
        </Card>
      )}

      {!jobsLoading &&
        !jobsError &&
        (Array.isArray(jobs) ? (
          <>
            {jobs.length > 0 ? (
              (() => {
                const grouped = (jobs as Jobs[]).reduce<Record<string, Jobs[]>>(
                  (acc, job) => {
                    const key = job?.status ?? "unknown";
                    (acc[key] ||= []).push(job);
                    return acc;
                  },
                  {},
                );

                const order: Array<keyof typeof grouped | "unknown"> = [
                  "running",
                  "pending",
                  "failed",
                  "completed",
                  "unknown",
                ];

                return order
                  .filter((status) => grouped[status as string]?.length)
                  .map((status) => (
                    <Stack key={status} mt="md">
                      <Group
                        justify="space-between"
                        wrap="nowrap"
                        style={{ cursor: "pointer" }}
                        onClick={() => toggleSection(status)}
                      >
                        <Group gap="xs">
                          <FontAwesomeIcon
                            icon={
                              collapsedSections[status]
                                ? faChevronDown
                                : faChevronUp
                            }
                            size="sm"
                            style={{ opacity: 0.5 }}
                          />
                          <Title order={3}>{startCase(status)}</Title>
                        </Group>
                        <Text size="xs" c="dimmed">
                          {grouped[status as string].length} job
                          {grouped[status as string].length > 1 ? "s" : ""}
                        </Text>
                      </Group>

                      <Collapse in={!collapsedSections[status]}>
                        <Stack>
                          {grouped[status as string]
                            .sort((a, b) => {
                              const timeA = new Date(
                                a?.last_run_time || 0,
                              ).getTime();
                              const timeB = new Date(
                                b?.last_run_time || 0,
                              ).getTime();
                              return timeB - timeA; // Latest first (descending order)
                            })
                            .map((job, index) => (
                              <Card
                                key={job?.job_id ?? `job-fallback-${index}`}
                                withBorder
                                radius="md"
                                padding="xs"
                                style={{
                                  backgroundColor:
                                    "var(--mantine-color-dark-6)",
                                }}
                              >
                                <Group
                                  gap="xs"
                                  align="flex-start"
                                  wrap="nowrap"
                                >
                                  {job?.is_progress && status !== "pending" && (
                                    <Tooltip
                                      label={`${job.progress_value}/${job.progress_max}`}
                                      position="right"
                                    >
                                      <RingProgress
                                        size={status === "running" ? 60 : 42}
                                        thickness={status === "running" ? 6 : 4}
                                        sections={[
                                          {
                                            value:
                                              job.progress_max > 0
                                                ? (job.progress_value /
                                                    job.progress_max) *
                                                  100
                                                : 0,
                                            color: "brand",
                                          },
                                        ]}
                                        label={
                                          <Text
                                            ta="center"
                                            size={
                                              status === "running"
                                                ? "xs"
                                                : "9px"
                                            }
                                            fw={700}
                                          >
                                            {job.progress_max > 0
                                              ? Math.round(
                                                  (job.progress_value /
                                                    job.progress_max) *
                                                    100,
                                                )
                                              : 0}
                                            %
                                          </Text>
                                        }
                                        className={
                                          status === "running"
                                            ? classes.pulse
                                            : undefined
                                        }
                                      />
                                    </Tooltip>
                                  )}
                                  <Stack
                                    gap={4}
                                    style={{ flex: 1, minWidth: 0 }}
                                  >
                                    <Group
                                      justify="space-between"
                                      gap="xs"
                                      wrap="nowrap"
                                    >
                                      <Text fw={500} size="sm" lineClamp={1}>
                                        {job?.job_name}
                                      </Text>
                                      <Group gap={4} style={{ flexShrink: 0 }}>
                                        {status === "pending" ? (
                                          <Menu position="bottom-end" withArrow>
                                            <Menu.Target>
                                              <ActionIcon
                                                variant="subtle"
                                                color="gray"
                                                size="sm"
                                              >
                                                <FontAwesomeIcon
                                                  icon={faEllipsis}
                                                />
                                              </ActionIcon>
                                            </Menu.Target>
                                            <Menu.Dropdown>
                                              <Menu.Item
                                                color="red"
                                                leftSection={
                                                  <FontAwesomeIcon
                                                    icon={faXmark}
                                                  />
                                                }
                                                onClick={() =>
                                                  job?.job_id &&
                                                  deleteJob(job.job_id)
                                                }
                                                disabled={isCancelling}
                                              >
                                                Cancel
                                              </Menu.Item>
                                            </Menu.Dropdown>
                                          </Menu>
                                        ) : (
                                          <Text size="xs" c="dimmed">
                                            <TimeAgo
                                              date={
                                                job?.last_run_time || new Date()
                                              }
                                              minPeriod={5}
                                            />
                                          </Text>
                                        )}
                                      </Group>
                                    </Group>
                                    {job?.progress_message && (
                                      <Text size="xs" c="dimmed" lineClamp={1}>
                                        {job.progress_message}
                                      </Text>
                                    )}
                                  </Stack>
                                </Group>
                              </Card>
                            ))}
                        </Stack>
                      </Collapse>
                    </Stack>
                  ));
              })()
            ) : (
              <Text c="dimmed" ta="center" py="xl">
                No jobs to display
              </Text>
            )}
          </>
        ) : (
          <Card withBorder padding="md" radius="sm">
            <Text size="sm" c="dimmed" mb="xs">
              Jobs
            </Text>
            <Text
              size="xs"
              style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
            >
              {typeof jobs === "string" ? jobs : JSON.stringify(jobs, null, 2)}
            </Text>
          </Card>
        ))}
    </Drawer>
  );
};

export default NotificationDrawer;
