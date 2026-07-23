import { FunctionComponent, useEffect, useMemo, useState } from "react";
import TimeAgo from "react-timeago";
import {
  ActionIcon,
  Badge,
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
  faCheck,
  faChevronDown,
  faChevronUp,
  faEllipsis,
  faPlay,
  faTowerBroadcast,
  faTurnDown,
  faTurnUp,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSystemJobs } from "@/apis/hooks";
import Jobs = System.Jobs;
import { showNotification } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startCase } from "lodash";
import { debounce } from "lodash";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { useModals } from "@/modules/modals";
import { notification } from "@/modules/task/notification";
import classes from "./JobsManager.module.css";

interface JobsManagerProps {
  opened: boolean;
  onClose: () => void;
}

const JobsManager: FunctionComponent<JobsManagerProps> = ({
  opened,
  onClose,
}) => {
  const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({});
  const modals = useModals();

  useEffect(() => {
    if (!opened) {
      setOpenMenus({});
    }
  }, [opened]);

  const handleMenuAction = (
    jobId: number,
    action: () => void,
    menuKey: string,
  ) => {
    setOpenMenus((prev) => ({ ...prev, [menuKey]: false }));
    setTimeout(() => action(), 50);
  };

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
      showNotification(
        notification.success(
          "Job Cancelled",
          "The job has been removed from the queue",
        ),
      );
    },
    onError: () => {
      showNotification(
        notification.error("Cancel Failed", "Unable to cancel the job"),
      );
    },
  });

  const { mutate: clearQueue } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Jobs, "clear"],
    mutationFn: (queueName: string) => api.system.clearJobs(queueName),
    onSuccess: (_, queueName) => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Jobs],
      });
      showNotification(
        notification.success(
          "Queue Cleared",
          `All ${queueName} jobs have been cleared`,
        ),
      );
    },
    onError: (_, queueName) => {
      showNotification(
        notification.error(
          "Clear Failed",
          `Unable to clear ${queueName} queue`,
        ),
      );
    },
  });

  const { mutate: actionOnJobs } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Jobs, "action"],
    mutationFn: (param: { id: number; action: string }) =>
      api.system.actionOnJobs(param.id, param.action),
    onSuccess: (_, variables) => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Jobs],
      });
      const actionLabels: Record<string, string> = {
        move_top: "Moved to top",
        move_bottom: "Moved to bottom",
        force_start: "Force started",
      };
      const label = actionLabels[variables.action] || "Action completed";
      showNotification(notification.success("Job Updated", label));
    },
    onError: () => {
      showNotification(
        notification.error(
          "Action Failed",
          "Unable to perform the requested action",
        ),
      );
    },
  });

  const debouncedActionOnJobs = useMemo(
    () => debounce(actionOnJobs, 300),
    [actionOnJobs],
  );

  const debouncedDeleteJob = useMemo(
    () => debounce(deleteJob, 300),
    [deleteJob],
  );

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

  const statusColors: Record<string, string> = {
    running: "info",
    pending: "warning",
    failed: "danger",
    completed: "success",
    unknown: "secondary",
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
          <Text c="danger.6" size="sm">
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
                        onClick={() => toggleSection(status)}
                        style={{ cursor: "pointer" }}
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
                          <Badge
                            color={statusColors[status] || "secondary"}
                            variant="light"
                            size="sm"
                          >
                            {grouped[status as string].length}
                          </Badge>
                          {status !== "running" && (
                            <div onClick={(e) => e.stopPropagation()}>
                              <Menu
                                position="bottom-end"
                                withArrow
                                opened={openMenus[`queue-${status}`] || false}
                                onChange={(opened) =>
                                  setOpenMenus((prev) => ({
                                    ...prev,
                                    [`queue-${status}`]: opened,
                                  }))
                                }
                              >
                                <Menu.Target>
                                  <ActionIcon
                                    variant="subtle"
                                    color="secondary"
                                    size="sm"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <FontAwesomeIcon icon={faEllipsis} />
                                  </ActionIcon>
                                </Menu.Target>
                                <Menu.Dropdown>
                                  <Menu.Item
                                    leftSection={
                                      <FontAwesomeIcon
                                        icon={faXmark}
                                        color="var(--mantine-color-danger-6)"
                                      />
                                    }
                                    onClick={() =>
                                      handleMenuAction(
                                        0,
                                        () =>
                                          modals.openConfirmModal({
                                            title: "Clear Queue",
                                            children: (
                                              <Text size="sm">
                                                Are you sure you want to clear
                                                all {startCase(status)} jobs
                                                from the queue?
                                              </Text>
                                            ),
                                            labels: {
                                              confirm: "Clear",
                                              cancel: "Cancel",
                                            },
                                            confirmProps: { color: "danger" },
                                            onConfirm: () => clearQueue(status),
                                          }),
                                        `queue-${status}`,
                                      )
                                    }
                                  >
                                    Clear this queue
                                  </Menu.Item>
                                </Menu.Dropdown>
                              </Menu>
                            </div>
                          )}
                        </Group>
                      </Group>

                      <Collapse expanded={!collapsedSections[status]}>
                        <Stack>
                          {grouped[status as string]
                            .slice()
                            .sort((a, b) => {
                              if (status === "pending") {
                                return 0; // Keep original order for pending jobs
                              }
                              // Sort by last_run_time descending (newest first)
                              const aTime = a?.last_run_time
                                ? new Date(a.last_run_time).getTime()
                                : 0;
                              const bTime = b?.last_run_time
                                ? new Date(b.last_run_time).getTime()
                                : 0;
                              return bTime - aTime;
                            })
                            .map((job, index) => (
                              <Card
                                key={`job-${job?.job_id}-${job?.status}`}
                                withBorder
                                radius="md"
                                padding="xs"
                                className={classes.jobCard}
                                style={{
                                  borderLeftColor: `var(--mantine-color-${statusColors[status] || "secondary"}-6)`,
                                  borderLeftWidth: "3px",
                                }}
                              >
                                <Group
                                  gap="xs"
                                  align="flex-start"
                                  wrap="nowrap"
                                >
                                  {status === "pending" && (
                                    <Badge
                                      size="sm"
                                      variant="filled"
                                      color="warning"
                                      circle
                                    >
                                      {index + 1}
                                    </Badge>
                                  )}
                                  {status !== "pending" &&
                                    (job?.is_progress ? (
                                      <Tooltip
                                        label={`${job.progress_value}/${job.progress_max}`}
                                        position="right"
                                      >
                                        <RingProgress
                                          size={status === "running" ? 60 : 42}
                                          thickness={
                                            status === "running" ? 6 : 4
                                          }
                                          sections={[
                                            {
                                              value:
                                                status === "completed" &&
                                                job.progress_max == 0 &&
                                                job.progress_value == 0
                                                  ? 100
                                                  : job.progress_max > 0
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
                                              {status === "completed" &&
                                              job.progress_max == 0 &&
                                              job.progress_value == 0
                                                ? 100
                                                : job.progress_max > 0
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
                                    ) : (
                                      <Group
                                        justify="center"
                                        style={{ width: 42, height: 42 }}
                                      >
                                        {status === "completed" ? (
                                          <FontAwesomeIcon
                                            icon={faCheck}
                                            color="var(--mantine-color-success-6)"
                                            size="lg"
                                          />
                                        ) : status === "failed" ? (
                                          <FontAwesomeIcon
                                            icon={faXmark}
                                            color="var(--mantine-color-danger-6)"
                                            size="lg"
                                          />
                                        ) : (
                                          <Loader size="sm" />
                                        )}
                                      </Group>
                                    ))}
                                  <Stack
                                    gap={4}
                                    style={{ flex: 1, minWidth: 0 }}
                                  >
                                    <Group
                                      justify="space-between"
                                      gap="xs"
                                      wrap="nowrap"
                                    >
                                      <Tooltip label={`Job ID: ${job?.job_id}`}>
                                        <Text fw={500} size="sm">
                                          {job?.job_name}
                                        </Text>
                                      </Tooltip>
                                      {job?.is_signalr && (
                                        <Tooltip label={"Live event initiated"}>
                                          <FontAwesomeIcon
                                            icon={faTowerBroadcast}
                                          />
                                        </Tooltip>
                                      )}
                                      <Group gap={4} style={{ flexShrink: 0 }}>
                                        {status === "pending" ? (
                                          <Menu
                                            position="bottom-end"
                                            withArrow
                                            opened={
                                              openMenus[`job-${job?.job_id}`] ||
                                              false
                                            }
                                            onChange={(opened) =>
                                              setOpenMenus((prev) => ({
                                                ...prev,
                                                [`job-${job?.job_id}`]: opened,
                                              }))
                                            }
                                          >
                                            <Menu.Target>
                                              <ActionIcon
                                                variant="subtle"
                                                color="secondary"
                                                size="sm"
                                              >
                                                <FontAwesomeIcon
                                                  icon={faEllipsis}
                                                />
                                              </ActionIcon>
                                            </Menu.Target>
                                            <Menu.Dropdown>
                                              <Menu.Item
                                                leftSection={
                                                  <FontAwesomeIcon
                                                    icon={faTurnUp}
                                                  />
                                                }
                                                onClick={() =>
                                                  handleMenuAction(
                                                    job?.job_id || 0,
                                                    () =>
                                                      job?.job_id &&
                                                      debouncedActionOnJobs({
                                                        id: job.job_id,
                                                        action: "move_top",
                                                      }),
                                                    `job-${job?.job_id}`,
                                                  )
                                                }
                                              >
                                                Move to top
                                              </Menu.Item>
                                              <Menu.Item
                                                leftSection={
                                                  <FontAwesomeIcon
                                                    icon={faTurnDown}
                                                  />
                                                }
                                                onClick={() =>
                                                  handleMenuAction(
                                                    job?.job_id || 0,
                                                    () =>
                                                      job?.job_id &&
                                                      debouncedActionOnJobs({
                                                        id: job.job_id,
                                                        action: "move_bottom",
                                                      }),
                                                    `job-${job?.job_id}`,
                                                  )
                                                }
                                              >
                                                Move to bottom
                                              </Menu.Item>
                                              <Menu.Divider />
                                              <Menu.Item
                                                leftSection={
                                                  <FontAwesomeIcon
                                                    icon={faPlay}
                                                  />
                                                }
                                                onClick={() =>
                                                  handleMenuAction(
                                                    job?.job_id || 0,
                                                    () =>
                                                      job?.job_id &&
                                                      debouncedActionOnJobs({
                                                        id: job.job_id,
                                                        action: "force_start",
                                                      }),
                                                    `job-${job?.job_id}`,
                                                  )
                                                }
                                              >
                                                Force Start
                                              </Menu.Item>
                                              <Menu.Divider />
                                              <Menu.Item
                                                leftSection={
                                                  <FontAwesomeIcon
                                                    icon={faXmark}
                                                    color="var(--mantine-color-danger-6)"
                                                  />
                                                }
                                                onClick={() =>
                                                  handleMenuAction(
                                                    job?.job_id || 0,
                                                    () =>
                                                      modals.openConfirmModal({
                                                        title: "Cancel Job",
                                                        children: (
                                                          <Text size="sm">
                                                            Are you sure you
                                                            want to cancel this
                                                            job?
                                                          </Text>
                                                        ),
                                                        labels: {
                                                          confirm: "Cancel Job",
                                                          cancel: "Cancel",
                                                        },
                                                        confirmProps: {
                                                          color: "danger",
                                                        },
                                                        onConfirm: () =>
                                                          job?.job_id &&
                                                          debouncedDeleteJob(
                                                            job.job_id,
                                                          ),
                                                      }),
                                                    `job-${job?.job_id}`,
                                                  )
                                                }
                                                disabled={isCancelling}
                                              >
                                                Cancel
                                              </Menu.Item>
                                            </Menu.Dropdown>
                                          </Menu>
                                        ) : (
                                          <TimeAgo
                                            key={`job-timestamp-${job?.job_id}`}
                                            date={
                                              job?.last_run_time || new Date()
                                            }
                                            minPeriod={5}
                                          />
                                        )}
                                      </Group>
                                    </Group>
                                    {job?.progress_message && (
                                      <Text size="xs" c="dimmed">
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

export default JobsManager;
