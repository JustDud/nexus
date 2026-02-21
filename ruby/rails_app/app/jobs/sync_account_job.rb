# frozen_string_literal: true

module AcmePortal
  # Placeholder for an ActiveJob-style background task.
  class SyncAccountJob
    def perform(account_id)
      return nil if account_id.nil?

      "synced-#{account_id}"
    end
  end
end
